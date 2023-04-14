import socket
import threading

def client():
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = ('localhost', 8090)
    print('connecting to %s port %s' % server_address)
    sock.connect(server_address)

    try:
        # Send data
        message = 'This is the message from client %s' % threading.current_thread().name
        print('sending "%s"' % message)
        sock.sendall(message.encode('utf-8'))

        # Look for the response
        message_received = sock.recv(1024)
        print('received "%s"' % message_received)

    finally:
        print('closing socket')
        sock.close()

# Creating multiple threads
for i in range(10):
    t = threading.Thread(target=client, name="Thread %s" % i)
    t.start()

# Joining all threads
for t in threading.enumerate():
    if t is not threading.current_thread():
        t.join()
        