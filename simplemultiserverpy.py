import multiprocessing
import socket
import os
import time

def broadcast(ip, port, broadcast_message):
    # Create a UDP socket
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Send message on broadcast address
    broadcast_socket.sendto(str.encode(broadcast_message), (ip, port))
    broadcast_socket.close()

class Server(multiprocessing.Process):
    def __init__(self, server_socket,  client_address):
        super(Server, self).__init__()
        self.server_socket = server_socket
        # self.received_data = received_data
        self.client_address = client_address

    def run(self):
        # message = 'Hi ' + self.client_address[0] + ':' + str(self.client_address[1]) + '. This is server ' + str(os.getpid())+'. with server port' +str(server_port)
        message = 'Hi '
        # time.sleep(10)
        broadcast('127.255.255.255', server_port, message)
        # self.server_socket.sendto(message, ("localhost", 37020))
        # self.server_socket.sendto(str.encode(message), self.client_address)
        print('boradcast to client: ', message)


if __name__ == "__main__":
    

    # Bind the socket to the port
    MY_HOST = socket.gethostname()
    server_IP = socket.gethostbyname(MY_HOST)
    print('server_IP'+ server_IP)
    server_address = socket.gethostbyname(MY_HOST)
    server_port = 10002

    message = server_IP + ' sent a broadcast'
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Buffer size
    buffer_size = 1024

    server_socket.bind((server_address, server_port))
    

    while True:
        print('Server up and running at {}:{}'.format(server_address, server_port))
        # store the address of the socket sending the data
        # data, address = server_socket.recvfrom(buffer_size)
        # print('Received message \'{}\' at {}:{}'.format(data.decode(), address[0], address[1]))
        p = Server(server_socket,  server_address)
        p.start()
        p.join()
