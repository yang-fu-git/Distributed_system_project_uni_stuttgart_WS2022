import socket

# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
# TODO: replace server address in dynamic discovery
server_address = None
server_port = 10001

# Buffer size
buffer_size = 1024

message = 'Hi server!'

try:
    # Listening port
    BROADCAST_PORT = 64922

    # Local host information
    MY_HOST = socket.gethostname()
    MY_IP = socket.gethostbyname(MY_HOST)
    # Create a UDP socket
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set the socket to broadcast and enable reusing addresses
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind socket to address and port
    listen_socket.bind((MY_IP, BROADCAST_PORT))

    print("Listening to broadcast messages, My ip address is {}:{}".format(MY_IP, BROADCAST_PORT))

    addrList = []
    while True:
        data, addr = listen_socket.recvfrom(1024)
        addrList.append(addr)
        # print(addrList[len(addrList)-1] == addrList[0])
        if data:
            print("Received broadcast message:", data.decode())
        
        


finally:
    client_socket.close()
    print('Socket closed')

"""    while message != '':
        # Send data
        client_socket.sendto(message.encode(), (server_address, server_port))
        print('Sent to server: ', message)

        # Receive response
        print('Waiting for response...')
        data, server = client_socket.recvfrom(buffer_size)
        print('Received message from server: ', data.decode())

        message = input("Please enter message: ")"""
    
    
