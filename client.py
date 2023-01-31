import socket
import threading
import json
from prefix import *
import ast
class Client:
    def __init__(self):
        self.send_socket = None
        self.log = [(0,None)]
        self.mutex = threading.Lock()
        self.currentMessageSent = False
        self.client_address = ()
        self.first_msg = ""
        self.current_leader_addr = None

    def start(self):
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        client_ip = s.getsockname()[0]
        s.close()
        # Broadcast empty message to get port assigned.
        self.send_socket.sendto(str.encode(BROADCAST_MESSAGE_CLIENT), (BROADCAST_IP,BROADCAST_PORT))
        self.client_address = (client_ip, self.send_socket.getsockname()[1])
        self.first_msg = str(self.client_address) + " is online."
        self.send_socket.sendto(str.encode(CLIENT_REQUEST + self.first_msg), (BROADCAST_IP,BROADCAST_PORT))
        threading.Thread(target=self.listen, args=(),name='RecieveGroupMessage').start()
        while True:
            self.sendMessage()

    def listen(self):
         while True:
            data, addr = self.send_socket.recvfrom(1024)
            if data.decode("utf-8").startswith(GROUP_MESSAGE):
                # Deserialize and update latest group view from leader.
                response = {'result':True}
                request = json.loads(data.decode("utf-8")[len(GROUP_MESSAGE):])
                self.log = list(json.loads(request['messages']))
                self.send_socket.sendto(str.encode(GROUP_MESSAGE_ACK + json.dumps(response)), addr)
                self.printLatestMessages()

    def printLatestMessages(self):
        for x in range(10):
            print(x, end='\r')
        for i in range(10):
            if len(self.log)-1 > (9 - i):
                print(self.log[i - 10])
            else:
                print("\n")
        print('Write your message as' + str(self.send_socket.getsockname()) + ' :')

    def sendMessage(self):
        message = input('Write your message as' + str(self.send_socket.getsockname()) + ' :' )
        self.send_socket.sendto(str.encode(CLIENT_REQUEST + message), (BROADCAST_IP,BROADCAST_PORT))
        # threading.Thread(target=self.listenAck, args=(),name='RecieveMessage').start()
        # Wait for server confirmation.
        

if __name__ == "__main__":
    client = Client()
    client.start()
