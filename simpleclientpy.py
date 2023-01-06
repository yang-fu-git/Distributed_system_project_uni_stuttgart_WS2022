import socket

# Create a UDP socket


if __name__ == "__main__":
    

# Bind the socket to the port
    MY_HOST = socket.gethostname()
    client_IP = socket.gethostbyname(MY_HOST)
    print('client ip'+ client_IP)
    client_port = 10001

# Buffer size
    interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
    allips = [ip[-1][0] for ip in interfaces]
    buffer_size = 1024
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 64922
    client_socket.bind((client_IP, 64922))
    # client_socket.bind(('', client_port))
    message = 'Hi server!'
    print('client start')
    try:
    # Send data
        while True:
            data, addr = client_socket.recvfrom(1024)
            print('get broadcast message from {}:{}'.format(addr[0], addr[1]))
            print('Sent to server: ', message)
            
    # Receive response
    # print('Waiting for response...')
    # data, server = client_socket.recvfrom(buffer_size)
    # print('Received message from server: ', data.decode())

    finally:
        client_socket.close()
        print('Socket closed')
