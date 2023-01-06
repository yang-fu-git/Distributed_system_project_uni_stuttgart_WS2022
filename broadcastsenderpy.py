import socket


def broadcast(ip, port, broadcast_message):
    # Create a UDP socket
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Send message on broadcast address
    while True:
        broadcast_socket.sendto(str.encode(broadcast_message), (ip, port))
        data, addr = broadcast_socket.recvfrom(1024)
        print(f"this is listener_socket: %s" % (addr,))
        # print('send broadcast ')
        # broadcast_socket.close()


if __name__ == '__main__':
    # Broadcast address and port
    BROADCAST_IP = "192.168.0.255"
    BROADCAST_PORT = 37020

    # Local host information
    MY_HOST = socket.gethostname()
    MY_IP = socket.gethostbyname_ex(MY_HOST)[-1][-1]
    MY_IP_LOCAL = socket.gethostbyname(MY_HOST + ".")
    print(MY_IP)
    print(MY_IP_LOCAL)
    message = MY_IP + ' sent a broadcast'
    # listen_socket_1.sendto(str.encode(message), ("192.168.178.122",37020))
    # print('send to 192')
    # listen_socket.sendto(str.encode(message), ("127.0.1.1",37020))
    # print('send to 127')
    broadcast("192.168.178.255", BROADCAST_PORT, message)
    print('send broadcast ')

