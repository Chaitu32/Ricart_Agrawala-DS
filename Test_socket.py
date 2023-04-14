import socket

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', 8090)
print('starting up on %s port %s' % server_address)
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print('waiting for a connection')
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)

        # Receive the date from client
        data = connection.recv(1024)
        print('received "%s"' % data)

        # Send data to client
        connection.sendall("Hello from server".encode('utf-8'))
        print('sent data back to the client %s', client_address)



    finally:
        # Clean up the connection
        connection.close()