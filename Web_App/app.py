# app.py
from ast import Delete
from flask import Flask, request, render_template
import socket
import sys
import threading
import subprocess
app = Flask(__name__)

nodes = []  # list of all nodes in the distributed system
critical_nodes = []  # list of nodes currently in the critical section
node_ports = {}
num_count = 1
cur_port = 8091

# Declaring Main socket to create Master Node
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server_address = ('localhost', 8080)
# print(f"Starting up on {server_address[0]} port {server_address[1]}")
# sock.bind(server_address)


def execute_file(file_path, node_id):
    file_path = file_path.split()
    file_path = [str(i) for i in file_path]
    print(['python3'] + file_path)
    with open("../Node_Program/temp/"+str(node_id) + ".txt", 'w') as output:
        subprocess.call(['python3'] + file_path, stderr=output)


# Create a thread to listen for incoming connections
file_path = '../Node_Program/Master_Node.py'
t = threading.Thread(target=execute_file, args=(file_path, 0))
t.start()


def Create_Node(node_id, node_port, total_nodes):
    file_path = '../Node_Program/Node.py'
    file_path = file_path + " " + str(node_id) + " " + str(node_port) + " " + str(
        total_nodes)
    # + " > " + "../Node_Program/temp/"+str(node_id)+".txt"
    print(file_path)
    t = threading.Thread(target=execute_file, args=(file_path, node_id))
    t.start()
    return


def Delete_Node(node_id):
    global node_ports
    # Create sock for DELETE msg
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', node_ports[node_id]))
    sock.sendall("DELETE_NODE 0".encode('utf-8'))
    sock.close()
    del node_ports[node_id]

    return True


def BroadCast_AddNode(node_id):
    global node_ports
    # Create a socket for ADD_NODE msg
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for i in node_ports:
        if i != node_id:
            sock.connect(('localhost', node_ports[i]))
            sock.sendall(("ADD_NODE "+str(node_id)+" " +
                         str(node_ports[node_id])).encode('utf-8'))
            sock.close()


def Critial_Section_Msg(node_id):
    global node_ports
    # Create a socket for CRITICAL_SECTION msg
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', node_ports[node_id]))
    sock.sendall("CRITICAL_SECTION 0".encode('utf-8'))
    sock.close()

    return True


@app.route('/', methods=['GET', 'POST'])
def home():
    global cur_port
    global nodes
    global node_ports
    if request.method == 'POST':
        num_count = request.args.get('num_count', default=1, type=int)
        node = request.form['node']
        if node in nodes:
            return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count,
                                   message=f'{node} already exists in the system')
        nodes.append(node)
        node_ports[node] = cur_port
        print(nodes)
        print(node_ports)
        Create_Node(node, cur_port, len(nodes))
        cur_port += 1
        # Create a socket for sending Node info to new node
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for i in nodes:

            if int(i) != int(node):
                print(i, node)
                print(node, " is connecting to ", i, sep=" ")
                try:
                    sock.connect(('localhost', node_ports[node]))
                    sock.sendall(("ADD_NODE "+str(i)+" " +
                                  str(node_ports[i])).encode('utf-8'))
                    sock.close()
                except socket.error as e:
                    print(f'Failed to connect to {"fsfs"}:{i} - {e}')

        # Broadcast ADD_NODE to all nodes
        BroadCast_AddNode(node)
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count,
                               message=f'{node} added to the system')
    else:
        num_count = request.args.get('num_count', default=1, type=int)
        return render_template('index.html')


def Init_Critial(node_id):
    global critical_nodes
    global nodes

    if node_id in nodes and node_id not in critical_nodes:
        critical_nodes.append(node_id)
        Critial_Section_Msg(node_id)
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count,
                               message=f'{node_id} added to critical section')
    else:
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count,
                               message=f'{node_id} not found in the system or already in critical section')


@app.route('/add_critical', methods=['POST'])
def add_critical():
    global critical_nodes
    global nodes
    global num_count
    num_count = request.args.get('num_count', default=1, type=int)

    nodes_list = request.form.getlist('num')
    nodes_list = [int(i) for i in nodes_list]
    print("me")
    print(num_count)
    print(nodes_list)
    print("me")
    for node in nodes_list:
        # Create a thread to INIT_CRITICAL_SECTION
        if node in nodes:
            t = threading.Thread(target=Init_Critial, args=(node))
            t.start()
            critical_nodes.append(node)
    return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count,
                           message=f'{nodes_list} added to critical section')
    # num_elements = int(request.form['num_elements'])

    # # Create an empty list to store the array elements
    # array = []

    # # Loop through the number of elements and add each element to the array
    # for i in range(num_elements):
    #     element = request.form[f'element_{i}']
    #     array.append(element)

    # # Return the array as a string
    # return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count,
    #                        message=f'{nodes_list} added to critical section')


@app.route('/remove_critical', methods=['POST'])
def remove_critical():
    node = request.form['node']
    if node in critical_nodes:
        critical_nodes.remove(node)
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count,
                               message=f'{node} removed from critical section')
    else:
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count,
                               message=f'{node} not found in critical section')


@app.route('/remove_node', methods=['POST'])
def remove_node():
    node = request.form['node']
    if node in nodes:
        nodes.remove(node)
        if node in critical_nodes:
            critical_nodes.remove(node)
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count,
                               message=f'{node} removed from the system')
    else:
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count,
                               message=f'{node} not found in the system')


@app.route('/status', methods=['GET'])
def status():
    return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count,)


if __name__ == '__main__':
    app.run(debug=True)
