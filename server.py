import socket


class Server(object):
    # Define the host and port to listen on
    HOST = "localhost"

    PORT = 8000


# Create a socket to listen for incoming messages
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

# Create a dictionary to store the sockets of each connected node
    node_sockets = {}

# Define the function to send a message to a specific node

    def send_message(node, message):
        # Get the socket for the node
        s = node_sockets[node]

    # Serialize the message and send it over the socket
        s.sendall(serialize(message))

# Define the function to receive a message from any node

    def receive_message():
        # Accept a new connection from a node
        client_socket, address = server_socket.accept()

    # Add the socket to the dictionary of node sockets
        node_sockets[address] = client_socket

    # Receive and deserialize the message from the socket
        message = client_socket.recv(1024)
        return deserialize(message)

# Define functions to serialize and deserialize messages

    def serialize(message):
        # Replace this with your own serialization logic
        return message

    def deserialize(message):
        # Replace this with your own deserialization logic
        return message
