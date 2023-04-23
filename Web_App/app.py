# app.py
from ast import Delete
from email import message
from platform import node
from flask import Flask, request, render_template, redirect
import socket
import sys
import threading
import subprocess
from time import sleep


app = Flask(__name__)

nodes = []  # list of all nodes in the distributed system
critical_nodes = []  # list of nodes currently in the critical section
node_ports = {}
num_count = 1
cur_port = 8091

critNode = -1
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

    for i in node_ports:
        if i != node_id:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    global critNode
    if request.method == 'POST':
        num_count = request.args.get('num_count', default=1, type=int)
        node = request.form['node']
        if node in nodes:
            return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count, critNode=critNode,
                                   message=f'{node} already exists in the system')
        nodes.append(node)
        node_ports[node] = cur_port
        print(nodes)
        print(node_ports)
        Create_Node(node, cur_port, len(nodes))
        cur_port += 1
        # Create a socket for sending Node info to new node
        sleep(2)
        for i in nodes:
            print(i, node)
            if i != node:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(('localhost', node_ports[node]))
                sock.sendall(
                    ("ADD_NODE "+str(i)+" "+str(node_ports[i])).encode('utf-8'))
                sock.close()

        # Broadcast ADD_NODE to all nodes
        BroadCast_AddNode(node)
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count, critNode=critNode,
                               message=f'{node} added to the system')
    else:
        num_count = request.args.get('num_count', default=1, type=int)
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count, critNode=critNode,
                               message=f'added to the system')


def Init_Critial(node_id):
    global critical_nodes
    global nodes

    if node_id in nodes and node_id not in critical_nodes:
        critical_nodes.append(node_id)
        Critial_Section_Msg(node_id)


@app.route('/add_critical', methods=['POST'])
def add_critical():
    global critical_nodes
    global nodes
    global num_count
    array = [request.form[f'array-{i}'] for i in range(1, 11)]
    nodes_list = []
    for n in array:
        if n in nodes and n not in nodes_list:
            nodes_list.append(n)

    num_count = len(nodes_list)

    # nodes_list = [int(i) for i in nodes_list]
    print("me")
    print(num_count)
    print(nodes_list)
    print("me")
    for node in nodes_list:
        # Create a thread to INIT_CRITICAL_SECTION
        if node in nodes:
            t = threading.Thread(target=Init_Critial, args=(node,))
            t.start()
            # critical_nodes.append(node)
    print("me1")
    print(critical_nodes)
    print("me1")
    return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count, critNode=critNode,
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
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count, critNode=critNode,
                               message=f'{node} removed from critical section')
    else:
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count, critNode=critNode,
                               message=f'{node} not found in critical section')


@app.route('/remove_node', methods=['POST'])
def remove_node():
    node = request.form['node']
    if node in nodes:
        nodes.remove(node)
        if node in critical_nodes:
            critical_nodes.remove(node)
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count, critNode=critNode,
                               message=f'{node} removed from the system')
    else:
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count, critNode=critNode,
                               message=f'{node} not found in the system')


@app.route('/Critial_Node_Update', methods=['POST'])
def Update_Critial_Section():
    global critNode
    global critical_nodes
    global nodes

    node = request.form['node_id']
    print("Critial Node %s" % node)
    if node in critical_nodes:
        critNode = node
        critical_nodes.remove(node)

        print("fsfsfsfsfsfsfsfsfs", critNode, critical_nodes)

    return redirect("http://localhost:5000/status")


@app.route('/status', methods=['GET', 'POST'])
def status():
    global nodes
    global critical_nodes
    global critNode
    global num_count
    msg = 'Page refreshed.'
    if critNode in nodes:
        msg = '{critNode} is in Critical Section.'

    print("Critical Node %s" % critNode)
    return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes, num_count=num_count, critNode=critNode,
                           message=msg)


if __name__ == '__main__':
    app.run(debug=True)
