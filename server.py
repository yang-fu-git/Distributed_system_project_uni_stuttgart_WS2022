import multiprocessing
import socket
import sys
import enum
import logging
import random
import time
import time, threading
from queue import Queue
from datetime import datetime
import ast
from threading import Lock


# 3 servers come online at the same time and start voting process asap
def broadcast(ip, port,broadcast_message,broadcast_socket):
    # Create a UDP socket
    # Send message on broadcast address
    broadcast_socket.sendto(str.encode(broadcast_message), (ip, port))
    # broadcast_socket.close()

# amount of time a follower waits until becoming a candidate.
# Returns random election timeout between 150ms and 300ms, in unit of seconds.
def ELECTION_TIMEOUT():
    # return random.uniform(150,300) * 1e-2
    return 300*1e-2
# send heartbeat message on heartbeat timeout.
def HEARTBEAT_TIMEOUT():
    return 100* 1e-2

# TODO: heartbeet ack should have a timeout, in order to kick unhealthy server out.

BUFFER_SIZE = 1024
BROADCAST_IP = "192.168.178.255"
BROADCAST_PORT = 10001
BROADCAST_MESSAGE = 'I\'m a new participant.'
REQUEST_VOTE_MESSAGE_PREFIX = 'Please vote me:'
RESPONSE_VOTE_MESSAGE_PREFIX = 'Vote response:'
HEARTBEAT_MESSAGE = 'I\'m the leader at term:'
HEARTBEAT_ACK_MESSAGE = 'I\'m still online'


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
        self.group_view_temp = set()
        self.listen_socket = None
        self.send_socket = None
        self.initialize()
        logging.info("Server address: %s, Online servers: %s, Server state: %s", 
                    self.server_address,
                    self.group_view,
                    self.state)
        # If the current candidate has voted in current term.
        self.vote_granted = False
        # Received number of votes, including self-voted one.
        self.num_votes = 0
        # Candidate’s term, default as 0, will be updated to current term via recheiving heartbeat.
        self.term = 0
        

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
        # self.listen_socket.setblocking(0)
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
        time.sleep(1)
        threading.Thread(target=self.listenAtSenderPort, args=(),name='ListenAtSendeSocket').start()
        # TODO: consider periodic send broad cast.
        self.broadcastPort(BROADCAST_MESSAGE)
        self.server_address = (self.server_ip,self.send_socket.getsockname()[1])
        time.sleep(5)
        self.scheduleElectionTimeout()

            
    
    def scheduleElectionTimeout(self):
        self.election_timer = threading.Timer(ELECTION_TIMEOUT(), self.requestVote)
        self.election_timer.start()

    
    def scheduleHeartbeatTimeout(self):
        if len(self.group_view_temp) != 0:
            self.group_view = self.group_view_temp
            self.group_view.add(self.server_address)
            self.group_view_temp.clear()
        self.sendHeartbeat()
        self.heartbeat_timer = threading.Timer(HEARTBEAT_TIMEOUT(), self.scheduleHeartbeatTimeout)
        self.heartbeat_timer.start()


    def requestVote(self):
        self.term +=1
        logging.debug("Request vote %s for term %s.", self.server_address, self.term)
        self.num_votes +=1
        self.vote_granted = True
        self.state = SERVER_STATE.CANDIDATE
        # No need to send if the server is the single participent in the group.
        # if not self.leaderElected():
        self.sendMessageToGroup(REQUEST_VOTE_MESSAGE_PREFIX + str(self.term))
    
    # Send message to all servers in group_view.
    def sendMessageToGroup(self, message):
        for addr in self.group_view:
            if addr == self.server_address:
                continue
            self.send_socket.sendto(str.encode(message),addr)    

    # 1. Tell others I'm leader at .. term with groupview
    # 2. Send log replication to others
    
    def sendHeartbeat(self):
        heartbeat_message = HEARTBEAT_MESSAGE+'{}'.format(self.term) +':with group view:{}'.format(repr(self.group_view))
        self.sendMessageToGroup(heartbeat_message)

    # def listenForheartAckknowledge(listen_socket):
    #     activeServer=[]
    #     while datetime.now().strftime("%H:%M:%S")-sendHeartBeatTime.get().total_seconds()*1000<1:
    #         data, addr = listen_socket.recvfrom(1024) #non blocking
    #         if data:
    #             if data == 'I\'m the new follower':
    #                 print(f"follower: %s" % (addr,))
    #                 activeServer.append(addr[1])
    #             elif data == 'plz vote me':
    #                 broadcast_socket.sendto(str.encode(message), (local_IP, (addr,)[1]))
    #     onlineServers = activeServer

    def leaderElected(self):
        if self.num_votes >= (len(self.group_view)//2 +1):
            self.state = SERVER_STATE.LEADER
            self.election_timer.cancel()
            self.scheduleHeartbeatTimeout()
            logging.info('I am the leader! %s at term %s',self.server_address,self.term)
            self.vote_granted = False
            return True
        else:
            return False
        
    def broadcastPort(self,message):
        broadcast(BROADCAST_IP, BROADCAST_PORT,message,self.send_socket)  

    def listen(self):
        while True:
            data, addr = self.listen_socket.recvfrom(1024)
            # with self.mutex:
            if data.decode("utf-8").startswith(BROADCAST_MESSAGE):
                # During voting, ignore newly online server.
                if addr not in self.group_view:
                    self.group_view.add(addr)
                    logging.info("Add server paticipent: %s", addr)
                    logging.info("Current group view: %s", self.group_view)
            
  
    
    def listenAtSenderPort(self):
        while True:
            data, addr = self.send_socket.recvfrom(1024)
            # with self.mutex:
            # GET election related message
            if data.decode("utf-8").startswith(REQUEST_VOTE_MESSAGE_PREFIX):
                foreign_term = int(data.decode("utf-8").split(":")[1])
                if not self.vote_granted and foreign_term >= self.term:
                    self.term = foreign_term
                    self.send_socket.sendto(str.encode(RESPONSE_VOTE_MESSAGE_PREFIX + "{}".format(self.term)), addr)
                    self.vote_granted = True
                    # resets its election timeout.
                    if self.election_timer is not None:
                        self.election_timer.cancel()
                        logging.debug("On receiving request vote. %s state is alive %s", self.server_address, self.election_timer.is_alive())

                    if self.election_timer.finished:
                        self.scheduleElectionTimeout()
                        logging.debug("OnReceiving Request Vote Timer is rescheduled. %s", self.server_address)
            elif data.decode("utf-8").startswith(RESPONSE_VOTE_MESSAGE_PREFIX) and self.state == SERVER_STATE.CANDIDATE:
                foreign_term = int(data.decode("utf-8").split(":")[1])
                logging.debug("Get vote response: %s", foreign_term)
                if foreign_term == self.term:
                    self.num_votes +=1
                    self.leaderElected()  
            elif data.decode("utf-8").startswith(HEARTBEAT_MESSAGE):
                if addr == self.server_address: 
                    return
                # update log replication
                logging.info('heartbeat recieve from:%s,self addr: %s', addr,self.server_address)
                
                self.term = int(data.decode("utf-8").split(':')[1])
                # logging.error(data.decode("utf-8").split(':')[3])
                self.group_view = ast.literal_eval(data.decode("utf-8").split(':')[3])
                
                if self.election_timer is not None:
                    self.election_timer.cancel()
                    logging.debug("On receiving heartbeat Timer. %s state is alive %s", self.server_address, self.election_timer.is_alive())
                
                self.state = SERVER_STATE.FOLLOWER
                logging.info('Server at %s is a follower at term %s',self.server_address,self.term)
                self.vote_granted = False
                # send heartbeat Ack
                self.send_socket.sendto(str.encode(HEARTBEAT_ACK_MESSAGE),addr)
                self.scheduleElectionTimeout()
                if self.election_timer.finished:
                    self.scheduleElectionTimeout()
                    logging.debug("On receiving Heartbeat: Timer is rescheduled. %s", self.server_address)
            # deal with heartbeat_Ack
            elif data.decode("utf-8").startswith(HEARTBEAT_ACK_MESSAGE) and self.state == SERVER_STATE.LEADER:
                self.group_view_temp.add(addr) 


if __name__ == "__main__":
    server = Server()
    server.start()
    
    





