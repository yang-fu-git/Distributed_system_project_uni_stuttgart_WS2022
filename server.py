import multiprocessing
import socket
import os


class Server(multiprocessing.Process):
    def __init__(self, server_socket):
        super(Server, self).__init__()
        self.server_socket = server_socket
        self.client_address = None
        self.received_data = None


    def run(self):
        message = 'This is server ' + str(os.getpid())
        
        print(message)

        # Buffer size
        buffer_size = 1024

        while True: 
            data, address = self.server_socket.recvfrom(buffer_size)
            
            self.received_data = data
            self.client_address = address

            self.server_socket.sendto(str.encode(message), self.client_address)
            print('Server: {} received message \'{}\' at {}:{}'.format(str(os.getpid()), data.decode(), address[0], address[1]))

if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the port
    server_address = '127.0.0.1'
    server_port = 10001

    

    server_socket.bind((server_address, server_port))
    print('Server up and running at {}:{}'.format(server_address, server_port))

    # while(True):
    for i in range(3):
        
        p = Server(server_socket)
        p.start()
    # p.join()
