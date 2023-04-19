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
    0: 8080,
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
Critial_Section_Reqlist = {}
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
        RequestQueue.append((Timestamp, NodeId))

    else:
        # Send reply to the node
        connection.sendall("REPLY %s %s" %
                           (node_id, Local_time+1).encode('utf-8'))


def ReplyHandler(data, connection):
    print("Reply Handler")
    print(data)
    data = data.decode('utf-8')
    data = data.split(" ")

    NodeId = int(data[1])
    Timestamp = int(data[2])

    if Critial_Section == True:
        if Critial_Section_Time < Timestamp:
            Critial_Section_Reqlist[NodeId-1] = True


def AddNodeHandler(data, connection):
    print("Add Node Handler")
    print(data)
    data = data.decode('utf-8')
    data = data.split(" ")

    NodeId = int(data[1])
    NodePort = int(data[2])

    ports[NodeId] = NodePort

    # Critical Section
    if Critial_Section == True:
        # Send request to the new node
        NodeSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        NodeSock.connect(('localhost', NodePort))
        NodeSock.sendall("REQUEST %s %s" %
                         (node_id, Local_time).encode('utf-8'))
        NodeSock.close()

        # Add the node to the request queue
        Critial_Section_Reqlist[NodeId-1] = False


def CriticalSectionHandler(data, connection):
    print("Critical Section Handler")
    print(data)
    data = data.decode('utf-8')
    data = data.split(" ")

    if Critial_Section == False:
        Critial_Section = True
        Critial_Section_Time = Local_time
        for i in ports:
            if i != node_id:
                NodePort = ports[i]
                NodeSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                NodeSock.connect(('localhost', NodePort))
                NodeSock.sendall("REQUEST %s %s" %
                                 (node_id, Local_time).encode('utf-8'))
                NodeSock.close()

                Critial_Section_Reqlist[i-1] = False

    # Send reply to the master node
    connection.sendall("REQUESTS_SENT %s %s" %
                       (node_id, Local_time+1).encode('utf-8'))


def MsgHandler(data, connection):
    print("Message Handler")
    print(data)
    data = data.decode('utf-8')
    data = data.split(" ")

    if data[0] == "REQUEST":
        print("Request Message")

    elif data[0] == "REPLY":
        print("Reply Message")

    elif data[0] == "ADD_NODE":
        print("Add Node Message")

    elif data[0] == "CRITICAL_SECTION":
        print("Critical Section Message")

    elif data[0] == "DELETE_NODE" and data[1] == "0":
        print("SHUTDOWN")
        return "SHUTDOWN"

    return "OK"


while True:

    # Check for Critical Section
    if Critial_Section == True:
        Check_reply = True
        for i in Critial_Section_Reqlist:
            if Critial_Section_Reqlist[i] == False:
                Check_reply = False
                break

        if Check_reply == True:
            # Critical Section
            print("Critical Section")

            # Send message to the master node
            MasterSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            MasterSock.connect(('localhost', ports[0]))
            MasterSock.sendall("CRITICAL_SECTION_DONE %s %s" %
                               (node_id, Local_time).encode('utf-8'))
            MasterSock.close()

            # Reset the variables
            Critial_Section = False
            Critial_Section_Reqlist = {}
            Critial_Section_Time = 0

    # Check for Request Queue
    if Critial_Section == False and len(RequestQueue) > 0:
        # Get the first request
        Request = heapq.heappop(RequestQueue)

        # Send reply to the node
        NodePort = ports[Request[1]]
        NodeSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        NodeSock.connect(('localhost', NodePort))
        NodeSock.sendall("REPLY %s %s" %
                         (node_id, Local_time+1).encode('utf-8'))
        NodeSock.close()

    elif Critial_Section == True and len(RequestQueue) > 0:
        # Get the first request
        Request = heapq.heappop(RequestQueue)

        if Request[0] < Critial_Section_Time:
            # Send reply to the node
            NodePort = ports[Request[1]]
            NodeSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            NodeSock.connect(('localhost', NodePort))
            NodeSock.sendall("REPLY %s %s" %
                             (node_id, Local_time+1).encode('utf-8'))
            NodeSock.close()

    # Wait for a connection
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)

        # Receive the date from client
        data = connection.recv(1024)
        print('received "%s"' % data)

        # Analyze the data
        data = data.decode('utf-8')
        Return = MsgHandler(data, connection)

        if Return == "SHUTDOWN":
            break

    finally:
        # Clean up the connection
        connection.close()

        # Update local time
        UpdateLocalTime()


# Close the socket
sock.close()

exit(0)
