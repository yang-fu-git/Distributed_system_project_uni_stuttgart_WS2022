import threading
import time

# Define the list of nodes in the cluster
nodes = ["node1", "node2", "node3"]

# Create a dictionary to store the state of each node
node_states = {node: "follower" for node in nodes}

# Create a lock to protect the node states dictionary
lock = threading.Lock()

# Define the Raft main loop for each node
def run_node(node):
    # Set the initial state of the node to "follower"
    with lock:
        node_states[node] = "follower"
    
    # Run the Raft loop indefinitely
    while True:
        # Check the state of the node
        with lock:
            state = node_states[node]
        
        # If the node is a "follower", wait for a message from the leader
        if state == "follower":
            message = receive_message()
            
            # If the message is a "request vote" message, vote for the candidate
            if message["type"] == "request vote":
                with lock:
                    node_states[node] = "voted"
                send_message(message["candidate"], {"type": "vote granted"})
            
            # If the message is a "new leader" message, switch to the "follower" state
            elif message["type"] == "new leader":
                with lock:
                    node_states[node] = "follower"
        
        # If the node is a "candidate", send a "request vote" message to all other nodes
        # and wait for a response
        elif state == "candidate":
            votes_received = 0
            for other_node in nodes:
                if other_node != node:
                    send_message(other_node, {"type": "request vote"})
            
            while votes_received < len(nodes) // 2:
                message = receive_message()
                if message["type"] == "vote granted":
                    votes_received += 1
            
            # If the node has received a majority of votes, switch to the "leader" state
            with lock:
                node_states[node] = "leader"
                send_message(other_node, {"type": "new leader"})
        
        # If the node is the leader, send a "heartbeat" message to all other nodes
        elif state == "leader":
            for other_node in nodes:
                if other_node != node:
                    send_message(other_node, {"type": "heartbeat"})
            
        # Sleep for a short time before checking the state again
        time.sleep(0.1)

# Start a thread for each node
threads = []
for node in nodes:
    t = threading.Thread(target=run_node, args=(node,))
    t.start()
    threads.append(t)

# Wait for all threads to complete
for t in threads:
    t.join()
