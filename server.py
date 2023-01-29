import socket


def broadcast(ip, port, broadcast_message):
    # Create a UDP socket
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Send message on broadcast address
    broadcast_socket.sendto(str.encode(broadcast_message), (ip, port))
    broadcast_socket.close()


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
    server_port = -1

    # Buffer size
    buffer_size = 1024

    # Bind server socket:
    server_socket.bind((server_address, 0))
    server_port = server_socket.getsockname()[1]
    broadcast_address = server_address
    server = Server(server_socket)
    message = 'Hi client! This is server at {}:{}'.format(server_address, server_port)
    print(message)



    while True:
        data, address = server_socket.recvfrom(buffer_size)
