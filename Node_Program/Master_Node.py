import socket
import sys


def Message_handle(data):
    data = data.split()
    Message_type = data[0]
    Node_Id = data[1]

    if Message_type == "IN_CRITICAL_SECTION":
        print(Node_Id)


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 8080)
print('starting up on %s port %s' % server_address)
sock.bind(server_address)
sock.listen(1)
print("executing master")
while True:
    print('waiting for a connection')
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)
        data = connection.recv(1024)
        print('received "%s"' % data)
        Message_handle(data)
    finally:
        connection.close()
