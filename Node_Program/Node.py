import socket
import sys
import heapq
import requests
from time import sleep

sys.stdout = sys.stderr

arguments = sys.argv

if len(arguments) < 4:
    print("Usage: python3 Node.py <node_id> <node_port> <total_nodes>")
    exit(1)

# Get node id and port
node_id = arguments[1]
node_port = arguments[2]

# Ports Mapping
ports = {
    0: 8080,
}

# Create a TCP/IP socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the port
    server_address = ('localhost', int(node_port))
    print('starting up on %s port %s' % server_address)
    sock.bind(server_address)
    print("Server Binded to port %s" % node_port)

# Listen for incoming connections
    sock.listen(10)
except socket.error as e:
    print(f'Failed to bind to {"fsfs"}:{node_port} - {e}')


# Local Variables
Total_Nodes = int(arguments[3])
Local_time = 0
RequestQueue = []
Critial_Section = False  # tells whether i am in critical section or not
Critial_Section_Reqlist = {}  # requests from other nodes
Critial_Section_Time = 0  # amount of time spent in critical section


def UpdateLocalTime():
    global Local_time
    Local_time += 1
    print("Local Time: %s" % Local_time)


def RequestHandler(data):
    global Local_time
    global RequestQueue
    global Critial_Section
    print("Request Handler")
    print(data)
    data = data.split(" ")

    NodeId = int(data[1])
    Timestamp = int(data[2])

    if Timestamp >= Local_time:
        Local_time = Timestamp

    if Timestamp >= Critial_Section_Time and Critial_Section == True:
        RequestQueue.append((Timestamp, NodeId))
        print("Added %s to request_queue with %s" % (NodeId, Timestamp))

    else:
        # Send reply to the node
        NodePort = ports[NodeId]
        try:
            NodeSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            NodeSock.connect(('localhost', NodePort))
            NodeSock.sendall(
                ("REPLY %s %s" % (node_id, Local_time+1)).encode('utf-8'))
            NodeSock.close()
            print("Sending reply to node %s" % NodeId)
        except ConnectionRefusedError:
            # Print error message
            print("Node %s is not available" % NodeId)
            print("Error Message: %s" % ConnectionRefusedError)
            del ports[NodeId]


def ReplyHandler(data):
    global Local_time
    global Critial_Section
    global Critial_Section_Reqlist
    global Critial_Section_Time
    print("Reply Handler")
    print(data)
    data = data.split(" ")

    NodeId = int(data[1])
    Timestamp = int(data[2])

    if Critial_Section == True:
        if Critial_Section_Time < Timestamp:
            Critial_Section_Reqlist[NodeId] = True


def AddNodeHandler(data):
    global Local_time
    global Critial_Section
    global Critial_Section_Reqlist

    print("Add Node Handler")
    print(data)
    data = data.split(" ")

    NodeId = int(data[1])
    NodePort = int(data[2])

    ports[NodeId] = NodePort

    # Critical Section
    if Critial_Section == True:
        # Send request to the new node
        NodeSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Try to connect to the node
        try:
            NodeSock.connect(('localhost', NodePort))
            NodeSock.sendall(("REQUEST %s %s" %
                             (node_id, Local_time)).encode('utf-8'))
            NodeSock.close()
            # Add the node to the request queue
            Critial_Section_Reqlist[NodeId] = False
        except ConnectionRefusedError:
            # Print error message
            print("Node %s is not available" % NodeId)
            print("Error Message: %s" % ConnectionRefusedError)
            # If the node is not available, remove it from the request queue
            del Critial_Section_Reqlist[NodeId]
            del ports[NodeId]

    # Send reply to the master node
    MasterSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    MasterSock.connect(('localhost', ports[0]))
    MasterSock.sendall(("NODE_ADDED %s %s %s" %
                       (node_id, Local_time+1, NodeId)).encode('utf-8'))
    MasterSock.close()


def CriticalSectionHandler(data):
    global Local_time
    global Critial_Section
    global Critial_Section_Reqlist
    global Critial_Section_Time
    global node_id

    print("Critical Section Handler")
    print(data)
    data = data.split(" ")

    if Critial_Section == False:
        Critial_Section = True
        Critial_Section_Time = Local_time
        Temp_ports = ports.copy()
        for i in Temp_ports:
            if i != node_id and i != 0:
                print("Sending request to node %s" % i)
                NodePort = ports[i]
                NodeSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    NodeSock.connect(('localhost', NodePort))
                    NodeSock.sendall(("REQUEST %s %s" %
                                    (node_id, Local_time)).encode('utf-8'))
                    NodeSock.close()
                    print("Request sent to node %s" % i)

                    Critial_Section_Reqlist[i] = False
                except ConnectionRefusedError:
                    # Print error message
                    print("Node %s is not available" % i)
                    print("Error Message: %s" % ConnectionRefusedError)
                    # If the node is not available, remove it from the request queue
                    if i in Critial_Section_Reqlist:
                        del Critial_Section_Reqlist[i]
                    del ports[i]

    # Send reply to the master node
    MasterSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    MasterSock.connect(('localhost', ports[0]))
    MasterSock.sendall(("REQUESTS_SENT %s %s" %
                       (node_id, Local_time+1)).encode('utf-8'))
    MasterSock.close()


def MsgHandler(data):
    print("Message Handler")
    print(data)
    data = data.split(" ")

    if data[0] == "REQUEST":
        print("Request Message")
        RequestHandler(' '.join(data))

    elif data[0] == "REPLY":
        print("Reply Message")
        ReplyHandler(' '.join(data))

    elif data[0] == "ADD_NODE":
        print("Add Node Message")
        AddNodeHandler(' '.join(data))

    elif data[0] == "CRITICAL_SECTION":
        print("Critical Section Message")
        CriticalSectionHandler(' '.join(data))

    elif data[0] == "DELETE_NODE" and data[1] == "0":
        print("SHUTDOWN")
        return "SHUTDOWN"

    return "OK"


while True:

    # Check for Critical Section
    if Critial_Section == True:
        Check_reply = True
        for i in Critial_Section_Reqlist:
            if Critial_Section_Reqlist[i] == False and  i in ports:
                Check_reply = False
                break

        if Check_reply == True:
            # Critical Section
            print("Critical Section")

            # Send Post request to Flask server
            url = "http://localhost:5000/Critial_Node_Update"
            res = requests.post(url, data={'node_id': node_id})

            print("Web Server is updated by %s" % node_id)
            sleep(20)

            res = requests.post(url, data={'node_id': -1})
            print("Web Server is updated by %s" % node_id)
            sleep(1)
            # Send message to the master node
            MasterSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            MasterSock.connect(('localhost', ports[0]))
            MasterSock.sendall(("IN_CRITICAL_SECTION %s %s" %
                               (node_id, Local_time)).encode('utf-8'))
            MasterSock.close()

            # Reset the variables
            Critial_Section = False
            Critial_Section_Reqlist = {}
            Critial_Section_Time = 0

            # Update the local time
            UpdateLocalTime()
            print("Critical Section Done %s" % node_id)

    # Check for Request Queue
    if Critial_Section == False and len(RequestQueue) > 0:
        # Get the first request
        while len(RequestQueue) > 0:
            heapq.heapify(RequestQueue)
            Request = heapq.heappop(RequestQueue)

            # Send reply to the node
            NodePort = ports[Request[1]]
            NodeSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            NodeSock.connect(('localhost', NodePort))
            NodeSock.sendall(
                ("REPLY %s %s" % (node_id, Local_time+1)).encode('utf-8'))
            NodeSock.close()

            # Update the local time
            UpdateLocalTime()
            print("Sent Reply to %s" % Request[1])

    elif Critial_Section == True and len(RequestQueue) > 0:
        # Get the first request
        heapq.heapify(RequestQueue)
        Request = heapq.heappop(RequestQueue)
        print(Request)

        if Request[0] == Critial_Section_Time and int(Request[1]) < int(node_id):
            # Send reply to the node
            NodePort = ports[Request[1]]
            NodeSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            NodeSock.connect(('localhost', NodePort))
            NodeSock.sendall(
                ("REPLY %s %s" % (node_id, Local_time+1)).encode('utf-8'))
            NodeSock.close()

            # Update the local time
            UpdateLocalTime()
            print("Sent Reply to %s" % Request[1])
        else:
            RequestQueue.append(Request)

    # Wait for a connection
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)

        # Receive the date from client
        data = connection.recv(1024)
        print('received "%s"' % data)
        connection.close()
        # Analyze the data
        data = data.decode('utf-8')
        Return = MsgHandler(data)

        if Return == "SHUTDOWN":
            break

    finally:
        print("Closing the connection")
        # Clean up the connection
        # connection.close()

        # Update local time
        UpdateLocalTime()


# Close the socket
sock.close()
print("Socket Closed Successfully")

# Send message to the master node
MasterSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
MasterSock.connect(('localhost', ports[0]))
MasterSock.sendall(("Node %s is shutdown" % node_id).encode('utf-8'))
MasterSock.close()

print("Node %s is shutdown" % node_id)

# Exit the program
exit(0)
