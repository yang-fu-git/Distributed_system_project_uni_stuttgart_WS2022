import socket



if __name__ == '__main__':
    # Listening port
    BROADCAST_PORT = 37020

    # Local host information
    MY_HOST = socket.gethostname()
    print(MY_HOST)
    # MY_LOOP_IP = socket.gethostbyname(MY_HOST)
    # print(MY_LOOP_IP)
    MY_IP_LOCAL = socket.gethostbyname(MY_HOST + ".")
    print(MY_IP_LOCAL)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    print(s.getsockname()[0])
    # Create a UDP socket
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set the socket to broadcast and enable reusing addresses
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind socket to address and port address is 192.168.178.122
    listen_socket.bind(('', BROADCAST_PORT))
    
    print("Listening to broadcast messages")

    while True:
        data, addr = listen_socket.recvfrom(1024)
        message = 'listener send message'
        
        if data:
            listen_socket.sendto(str.encode(message), ("192.168.178.122",addr[1]))
            print("Received broadcast message:",addr)
