import socket
import sys
import heapq

arguments = sys.argv

if len(arguments) < 4:
    print("Usage: python3 Node.py <node_id> <node_port> <total_nodes>")
    exit(1)

# Get node id and port
node_id = arguments[1]
node_port = arguments[2]

# Ports Mapping
ports = {
    1: 8090,
    2: 8091,
    3: 8092,
    4: 8093,
}

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', int(node_port))
print('starting up on %s port %s' % server_address)
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

# Local Variables
Total_Nodes = int(arguments[3])
Local_time = 0
RequestQueue = []
Critial_Section = False
Critial_Section_Reqlist = [False]*Total_Nodes
Critial_Section_Time = 0


def UpdateLocalTime():
    global Local_time
    Local_time += 1

def RequestHandler(data, connection):
    print("Request Handler")
    print(data)
    data = data.decode('utf-8')
    data = data.split(" ")

    NodeId = int(data[1])
    Timestamp = int(data[2])

    if Timestamp > Local_time:
        Local_time = Timestamp
        RequestQueue.append((Timestamp,NodeId))

    else:
        # Send reply to the node
        connection.sendall("REPLY %s %s" % (node_id, Local_time+1).encode('utf-8'))

def ReplyHandler(data, connection):
    print("Reply Handler")
    print(data)
    data = data.decode('utf-8')
    data = data.split(" ")

    NodeId = int(data[1])
    Timestamp = int(data[2])

    if Critial_Section==True:
        if Critial_Section_Time < Timestamp:
            Critial_Section_Reqlist[NodeId-1] = True





def MsgHandler(data, connection):
    print("Message Handler")
    print(data)
    data = data.decode('utf-8')
    data = data.split(" ")

    if data[0] == "REQUEST":
        print("Request Message")

    elif data[0] == "REPLY":
        print("Reply Message")
        

while True:
    # Wait for a connection
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)

        # Receive the date from client
        data = connection.recv(1024)
        print('received "%s"' % data)

        # Analyze the data
        data = data.decode('utf-8')
