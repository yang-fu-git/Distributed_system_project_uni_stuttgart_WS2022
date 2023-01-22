import socket

CLIENT_REQUEST = "Client request:"
CLIENT_RESPONSE = "Client response:"
BROADCAST_IP = "192.168.178.255"
BROADCAST_PORT = 10001

send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

send_socket.sendto(str.encode(CLIENT_REQUEST + "Ok"), (BROADCAST_IP,BROADCAST_PORT))