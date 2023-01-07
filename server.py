import socket
import time
from threading import Thread

def broadcast(ip, port, broadcast_message):
    # Create a UDP socket
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Send message on broadcast address
    broadcast_socket.sendto(str.encode(broadcast_message), (ip, port))
    print('broadcast message sent.')
    broadcast_socket.close()


def getBroadcastIP(MY_IP):
    ip = MY_IP.split('.')
    BROADCAST_IP = ip[0] + '.' + ip[1] + '.' + ip[2] + '.255'
    return BROADCAST_IP

def sendHeartbeat(bIP, port, mIP):
    msg = 'Alive: ' + mIP
    while True:
        broadcast(bIP, port, msg)
        time.sleep(1)

class Server:
    def __init__(self, server_socket):
        self.server_socket = server_socket
        self.isFollower = True
        self.isCandidate = False
        self.isLeader = False


if __name__ == '__main__':
    # create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Server application IP address and port
    MY_HOST = socket.gethostname()
    server_address = socket.gethostbyname(MY_HOST)
    # server_port = -1
    server_port = 64922

    # Buffer size
    buffer_size = 1024
    
    # Broadcast address and port
    BROADCAST_IP = getBroadcastIP(server_address)

    # Send broadcast message
    sendHeartbeatMsg = Thread(target=sendHeartbeat, args = (BROADCAST_IP, server_port, server_address))
    sendHeartbeatMsg.start()

    
"""    message = MY_HOST + ' sent a broadcast'
    broadcast(BROADCAST_IP, BROADCAST_PORT, message)"""


"""    # Bind server socket:
    server_socket.bind((server_address, 0))
    server_port = server_socket.getsockname()[1]
    broadcast_address = server_address
    server = Server(server_socket)
    message = 'Hi client! This is server at {}:{}'.format(server_address, server_port)
    print(message)



    while True:
        data, address = server_socket.recvfrom(buffer_size)"""
