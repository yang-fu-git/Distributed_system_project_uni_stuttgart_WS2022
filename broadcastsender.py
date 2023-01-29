import socket


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
    

if __name__ == '__main__':

    # Local host information
    MY_HOST = socket.gethostname()
    MY_IP = socket.gethostbyname(MY_HOST)

    # Broadcast address and port
    BROADCAST_IP = getBroadcastIP(MY_IP)
    
    print('ip:{}, broadcast address:{}'.format(MY_IP, BROADCAST_IP))
    BROADCAST_PORT = 64922

    # Send broadcast message
    message = MY_IP + ' sent a broadcast'
    broadcast(BROADCAST_IP, BROADCAST_PORT, message)

