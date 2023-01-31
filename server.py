import socket
import sys
import enum
import logging
import random
import time, threading
from queue import Queue
from datetime import datetime
import json
import ast
import collections
from threading import Lock
from prefix import *
import os

# 3 servers come online at the same time and start voting process asap
def broadcast(ip, port,broadcast_message,broadcast_socket):
    # Create a UDP socket
    # Send message on broadcast address
    broadcast_socket.sendto(str.encode(broadcast_message), (ip, port))
    # broadcast_socket.close()

# amount of time a follower waits until becoming a candidate.
# Returns random election timeout between 150ms and 300ms, in unit of seconds.
def ELECTION_TIMEOUT():
    return random.uniform(150,300) * 1e-2
# send heartbeat message on heartbeat timeout.
def HEARTBEAT_TIMEOUT():
    return 100* 1e-2

# TODO: heartbeat ack should have a timeout, in order to kick unhealthy server out.

class SERVER_STATE(enum.Enum):
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3

class Server:
    def __init__(self):
        super(Server, self).__init__()
        self.mutex = Lock()
        # Redirect logging to stdout.
        self.logger = None
        # In which state the current server is in. Default as `FOLLOWER` 
        self.state = SERVER_STATE.FOLLOWER
        # String ecoded by (`ip_address`,`port`) tuple.
        self.server_address = ()
        self.server_ip = ''
        # List of all distinct online servers. Key of online server is server_address.
        self.group_view = set()
        self.group_view_ack = set()

        self.client_view = set()
        self.client_view_ack = set()
        self.client_view_unhealthy = collections.Counter()

        # Number of unacks of unhealthy online servers, only valid for leader.
        # Servers that did not acknowledge are considered as unhealthy and its correspinding number will be incremented.
        # Unhealthy servers with unacked number >= UNACK_THREASHOLD will be removed.
        self.group_view_unhealthy = collections.Counter()
        self.listen_socket = None
        self.send_socket = None
        self.initialize()
        logging.info("Server address: %s, Online servers: %s, Server state: %s", 
                    self.server_address,
                    self.group_view,
                    self.state)
        # If the current candidate has voted in current term.
        self.voted_for = None
        # Received number of votes, including self-voted one.
        self.num_votes = 0
        # Candidate’s term, default as 0, will be updated to current term via recheiving heartbeat.
        self.term = 0
        # Store the address for the current leader.
        self.current_leader_addr = None

        # Log entries; each entry contains command for state machine, and term when entry was received by leader
        # (first index is 1).
        # LogEntry: (LogTerm, LogContent)
        self.log = [(0,None)]
        # Volatile state on all servers.
        # index of highest log entry known to be committed (initialized to 0, increases monotonically)
        self.commit_index = 0
        # index of highest log entry applied to state machine (initialized to 0, increases monotonically)
        self.last_applied = 0

        # Volatile state on leaders:

        # for each server, index of the next log entry
        # to send to that server (initialized to leader
        # last log index + 1)
        self.next_index = {}

        # for each server, index of highest log entry
        # known to be replicated on server
        # (initialized to 0, increases monotonically)
        self.match_index = {}
        

    def initialize(self):
        # Trick to initialize local IP.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.server_ip = s.getsockname()[0]
        s.close()
        # Initialize sockets.
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Trick: '' in fact bind to real server local ip.
        self.listen_socket.bind(('', BROADCAST_PORT))
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Configure logger.
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter) 
        self.logger.addHandler(handler)
        # Handle for election timer.
        self.election_timer = None
        # Handle for heartbeat timer.
        self.heartbeat_timer = None

    def start(self):
        threading.Thread(target=self.listen, args=(),name='ListenToBroadcastThread').start()
        threading.Thread(target=self.listenAtSenderPort, args=(),name='ListenAtSendeSocket').start()
        # TODO: consider periodic send broad cast.
        self.broadcastPort(BROADCAST_MESSAGE)
        self.server_address = (self.server_ip,self.send_socket.getsockname()[1])
        self.scheduleElectionTimeout()
    
    def scheduleElectionTimeout(self):
        if self.election_timer is not None:
            self.election_timer.cancel()
        self.election_timer = threading.Timer(ELECTION_TIMEOUT(), self.requestVote)
        self.election_timer.start()

    
    def scheduleHeartbeatTimeout(self):
        # Update group view in case any participant is unhealthy.
        self.group_view_ack.add(self.server_address)
        # Reset if server is healthy again.
        for acked in self.group_view_ack:
            del self.group_view_unhealthy[acked]
        # Kick out unhealthy server.
        for unacked in self.group_view.difference(self.group_view_ack):
            self.group_view_unhealthy[unacked] += 1
            if self.group_view_unhealthy[unacked] == UNACK_THREASHOLD:
                self.group_view.remove(unacked)
                self.next_index.pop(unacked, None)
                self.match_index.pop(unacked, None)
        self.group_view_ack.clear()
        logging.debug("Updated group view before heartbeat: %s", self.group_view)
        self.appendEntries()
        self.heartbeat_timer = threading.Timer(HEARTBEAT_TIMEOUT(), self.scheduleHeartbeatTimeout)
        self.heartbeat_timer.start()

    def pushMessagesToClients(self):
        # Update list of clients if needed.
        # Reset if server is healthy again.
        for acked in self.client_view_ack:
            del self.client_view_unhealthy[acked]
        # Kick out unhealthy server.
        for unacked in self.client_view.difference(self.client_view_ack):
            self.client_view_unhealthy[unacked] += 1
            if self.client_view_unhealthy[unacked] == UNACK_THREASHOLD:
                self.client_view.remove(unacked)
        self.client_view_ack.clear()
        for addr in self.client_view:
            push_messages_payload = {
                'messages': json.dumps([msg for (_, msg) in self.log[1:]]),
            }
            message = GROUP_MESSAGE+'{}'.format(json.dumps(push_messages_payload))
            self.send_socket.sendto(str.encode(message),addr)

    def requestVote(self):
        # If leader is unhealthy, we should at least remove leader from group view.
        if self.current_leader_addr != self.server_address and self.current_leader_addr in self.group_view:
            self.group_view.remove(self.current_leader_addr)
            self.next_index.pop(self.current_leader_addr, None)
            self.match_index.pop(self.current_leader_addr, None)
        self.num_votes = 0
        # Increment current term.
        self.term +=1
        logging.info("RequestVote at %s at term %s with group %s", self.server_address, self.term, self.group_view)
        # Vote for self.
        self.num_votes +=1
        self.voted_for = self.server_address
        self.state = SERVER_STATE.CANDIDATE
        # No need to send if the server is the single participent in the group.
        if not self.leaderElected():
            # Reset election timer.
            self.scheduleElectionTimeout()
            # Send RequestVote RPCs to all other servers.
            for addr in self.group_view:
                if addr == self.server_address:
                    continue
                self.send_socket.sendto(str.encode(REQUEST_VOTE_MESSAGE_PREFIX + str(self.term)),addr)
            

    # 1. Tell others I'm leader at .. term with groupview
    # 2. Send log replication to others
    def appendEntries(self):
        logging.info("Leader with PID %s log entries: %s", os.getpid(), self.log)
        # with self.mutex:
        # If there exists an N such that N > commitIndex, a majority
        # of matchIndex[i] ≥ N, and log[N].term == currentTerm:
        # set commitIndex = N
        while self.commit_index + 1 < len(self.log):
            # Including leader itself -> +1
            num_matched = 1+sum(1 for (_,match_idx) in self.match_index.items() if match_idx > self.commit_index)
            if num_matched > len(self.match_index)/2 and self.log[self.commit_index+1][0] == self.term:
                self.commit_index += 1
            else:
                break
        if self.last_applied < self.commit_index:
            self.last_applied = self.commit_index
            self.pushMessagesToClients()
        
        for addr in self.group_view:
            if addr == self.server_address:
                continue
            append_entries_payload = {
                'term':self.term,
                'leaderId':self.server_address,
                'prevLogIndex':self.next_index[addr]-1,
                'prevLogTerm':self.log[self.next_index[addr]-1][0],
                'entries':[],
                'leaderCommit':self.commit_index,
                'group_view':repr(self.group_view),
                'client_view':repr(self.client_view) if len(self.client_view)>0 else "[]"
            }
            if self.next_index[addr] < len(self.log):
                append_entries_payload['entries'] = self.log[self.next_index[addr]:]
            message = HEARTBEAT_MESSAGE+'{}'.format(json.dumps(append_entries_payload))
            self.send_socket.sendto(str.encode(message),addr)
        

    def leaderElected(self):
        if self.num_votes >= (len(self.group_view)//2 +1):
            self.state = SERVER_STATE.LEADER
            # Initialize all participant as healthy.
            self.group_view_ack = self.group_view.copy()
            if self.election_timer is not None:
                self.election_timer.cancel()
            logging.info('Leader elected at %s for term %s',self.server_address,self.term)
            self.has_voted = None
            # When a leader first comes to power,
            # it initializes all nextIndex values to the index just after the
            # last one in its log
            next_index = len(self.log)
            for addr in self.group_view:
                self.next_index[addr] = next_index
                self.match_index[addr] = 0
            self.scheduleHeartbeatTimeout()
            return True
        else:
            return False
        
    def broadcastPort(self,message):
        broadcast(BROADCAST_IP, BROADCAST_PORT,message,self.send_socket)  

    def listen(self):
        while True:
            data, addr = self.listen_socket.recvfrom(1024)
            if data.decode("utf-8").startswith(BROADCAST_MESSAGE):
                # During voting, ignore newly online server.
                if addr not in self.group_view:
                    self.group_view.add(addr)
                    self.next_index[addr] = len(self.log)
                    self.match_index[addr] = 0
                    logging.info("Add server paticipent: %s", addr)
                    logging.info("Current group view: %s", self.group_view)
            elif data.decode("utf-8").startswith(CLIENT_REQUEST):
                if self.state == SERVER_STATE.LEADER:
                    self.log.append([self.term,"Client message " + str(addr) + ": " + data.decode("utf-8").split(":")[1]])
            elif data.decode("utf-8").startswith(BROADCAST_MESSAGE_CLIENT):
                if self.state == SERVER_STATE.LEADER:
                    if addr not in self.client_view:
                        self.client_view.add(addr)

  
    
    def listenAtSenderPort(self):
        logging.info('listen at sender port start')
        while True:
            data, addr = self.send_socket.recvfrom(1024)
             # GET election related message
            if data.decode("utf-8").startswith(REQUEST_VOTE_MESSAGE_PREFIX):
                foreign_term = int(data.decode("utf-8").split(":")[1])
                # TODO Vote response based on log entry status.
                if foreign_term > self.term or (foreign_term == self.term 
                and (self.voted_for is None or self.voted_for == addr)):
                    self.term = foreign_term
                    self.send_socket.sendto(str.encode(RESPONSE_VOTE_MESSAGE_PREFIX + "{}".format(foreign_term)), addr)
                    self.voted_for = addr
                    # resets its election timeout.
                    self.scheduleElectionTimeout()
                
            elif data.decode("utf-8").startswith(RESPONSE_VOTE_MESSAGE_PREFIX) and self.state == SERVER_STATE.CANDIDATE:
                foreign_term = int(data.decode("utf-8").split(":")[1])
                logging.debug("Get vote response: %s", foreign_term)
                if foreign_term == self.term:
                    self.num_votes +=1
                    self.leaderElected()  
            elif data.decode("utf-8").startswith(HEARTBEAT_MESSAGE):
                if addr == self.server_address: 
                    return
                # Deserialize and update latest group view from leader.
                response = {'result':True}
                request = json.loads(data.decode("utf-8")[len(HEARTBEAT_MESSAGE):])
                logging.debug("Follower appendEntries request %s",request)
                self.group_view = ast.literal_eval(request['group_view'])
                if request['client_view'] != "[]":
                    self.client_view = ast.literal_eval(request['client_view'])
                if self.heartbeat_timer is not None:
                    self.heartbeat_timer.cancel()
                self.state = SERVER_STATE.FOLLOWER
                self.current_leader_addr = addr
                if self.term > request['term']:
                    # Reply false if foreign term < currentTerm
                    response['result'] = False
                elif len(self.log)<=request['prevLogIndex']:
                    # Reply false if log doesn’t contain an entry at prevLogIndex
                    # whose term matches prevLogTerm
                    response['result'] = False
                elif self.log[request['prevLogIndex']][0] != request['prevLogTerm']:
                    # If an existing entry conflicts with a new one (same index 
                    # but different terms), delete the existing entry and all that
                    # follow it
                    self.log = self.log[0:request['prevLogIndex']]
                    response['result'] = False
                else:
                    if len(request['entries']) > 0:
                        self.log = self.log[0:request['prevLogIndex']+1]
                        # Append any new entries not already in the log
                        self.log += request['entries']
                # If leaderCommit > commitIndex, set commitIndex =
                # min(leaderCommit, index of last new entry)
                if self.commit_index < request['leaderCommit']:
                    self.commit_index = max(request['leaderCommit'],len(self.log)-1)
                # If commitIndex > lastApplied: increment lastApplied, apply
                # log[lastApplied] to state machine
                if self.last_applied < self.commit_index:
                    self.last_applied = self.commit_index
                logging.info('Server at %s is a follower with PID %s with log entries: %s',self.server_address, os.getpid() , self.log)
                self.term = request['term']
                response['term'] = self.term
                self.has_voted = False
                # Reset election timer.
                self.scheduleElectionTimeout()
                self.send_socket.sendto(str.encode(HEARTBEAT_ACK_MESSAGE + json.dumps(response)), addr)
            # Deal with heartbeat_Ack.
            elif data.decode("utf-8").startswith(HEARTBEAT_ACK_MESSAGE) and self.state == SERVER_STATE.LEADER:
                request = json.loads(data.decode("utf-8")[len(HEARTBEAT_ACK_MESSAGE):])
                # logging.info("Leader %s received ack from %s.", self.server_address, addr)
                if request['term'] == self.term and request['result']:
                    self.match_index[addr] = len(self.log)
                    self.next_index[addr] = len(self.log)
                else:
                    self.next_index[addr] -= 1
                self.group_view_ack.add(addr)
            elif data.decode("utf-8").startswith(GROUP_MESSAGE_ACK) and self.state == SERVER_STATE.LEADER:
                request = json.loads(data.decode("utf-8")[len(GROUP_MESSAGE_ACK):])
                self.client_view_ack.add(addr)



if __name__ == "__main__":
    server = Server()
    server.start()
    
    





