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

# Redirect logging to stdout.
root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

# 3 servers come online at the same time and start voting process asap
def broadcast(ip, port,broadcast_message,broadcast_socket):
    # Create a UDP socket
    # Send message on broadcast address
    broadcast_socket.sendto(str.encode(broadcast_message), (ip, port))
    broadcast_socket.close()

# Returns random election timeout between 150ms and 300ms.
def ELECTION_TIMEOUT():
    return random.uniform(150,300)

def HEARTBEAT_TIMEOUT():
    return random.uniform(150,300)


BUFFER_SIZE = 1024
BROADCAST_IP = "192.168.178.255"
BROADCAST_PORT = 10001
BROADCAST_MESSAGE = 'I\'m a new participant.'

class SERVER_STATE(enum.Enum):
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3

class Server:
    def __init__(self):
        super(Server, self).__init__()
        # In which state the current server is in. Default as `FOLLOWER` 
        self.state = SERVER_STATE.FOLLOWER
        # String ecoded by `ip_address`_`port`.
        self.server_address = ''
        # List of all distinct online servers. Key of online server is server_address.
        self.group_view = set()
        self.listen_socket = None
        self.broadcast_socket = None
        self.initialize()
        logging.info("Server address: %s, Online servers: %s, Server state: %s", 
                    self.server_address,
                    self.group_view,
                    self.state)
        

    def initialize(self):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # This will then return immediately if there is no data available.
        # self.listen_socket.setblocking(0)
        # Trick: '' in fact bind to real server local ip.
        self.listen_socket.bind(('', BROADCAST_PORT))
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        
        # Start listening on broadcasted messages.
        
    def start(self):
        threading.Thread(target=self.listen, args=(),name='ListenToBroadcastThread').start()
        time.sleep(1)
        self.broadcastPort()

        
    
    # def sendVoteRequest(onlineServers,broadcast_socket):
    #     message = 'plz vote me'
    #     for port in onlineServers:
    #         broadcast_socket.sendto(str.encode(message), (local_IP, port))    

    # def sendHeartbeat():
    #     message_state = 'serverstate is'
    #     while True: 
    #         broadcast(BROADCAST_IP, BROADCAST_PORT, message_state)
    #         sendHeartBeatTime = sendHeartBeatTime.Queue()
    #         sendHeartBeatTime.put(datetime.now().strftime("%H:%M:%S"))
    #         time.sleep(1)

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
        
    def broadcastPort(self):
        broadcast_message = 'I\'m a new participant.'
        broadcast(BROADCAST_IP, BROADCAST_PORT,broadcast_message,self.broadcast_socket)  

    def listen(self):
        while True:
            data, addr = self.listen_socket.recvfrom(1024)
            print(data)
            if data:
                server_addr = "{0}_{1}".format(addr[0],addr[1])
                self.group_view.add(server_addr)
                logging.info("Add server paticipent: %s", server_addr)
                logging.info("Current group view: %s", self.group_view)


if __name__ == "__main__":
    # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # s.connect(("8.8.8.8", 80))
    # local_IP = s.getsockname()[0]
    # print('server_IP'+ local_IP)
 
    server = Server()
    server.start()

    





