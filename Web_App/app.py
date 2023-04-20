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

# Declaring Main socket to create Master Node
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server_address = ('localhost', 8080)
# print(f"Starting up on {server_address[0]} port {server_address[1]}")
# sock.bind(server_address)


def execute_file(file_path):
    subprocess.call(['python3', file_path])


# Create a thread to listen for incoming connections
file_path = '../Node_Program/Master_Node.py'
t = threading.Thread(target=execute_file, args=(file_path,))
t.start()


def Create_Node(node_id, node_port, total_nodes):
    file_path = '../Node_Program/Node.py'
    file_path = file_path + " " + \
        str(node_id) + " " + str(node_port) + " " + str(total_nodes)
    t = threading.Thread(target=execute_file, args=(file_path))
    t.start()
    return


def Delete_Node(node_id):
    # Create sock for DELETE msg
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', node_ports[node_id]))
    sock.sendall("DELETE_NODE 0".encode('utf-8'))
    sock.close()
    del node_ports[node_id]

    return True


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        node = request.form['node']
        nodes.append(node)
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes,
                               message=f'{node} added to the system')
    else:
        return render_template('index.html')


@app.route('/add_critical', methods=['POST'])
def add_critical():
    node = request.form['node']
    if node in nodes and node not in critical_nodes:
        critical_nodes.append(node)
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes,
                               message=f'{node} added to critical section')
    else:
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes,
                               message=f'{node} not found in the system or already in critical section')


@app.route('/remove_critical', methods=['POST'])
def remove_critical():
    node = request.form['node']
    if node in critical_nodes:
        critical_nodes.remove(node)
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes,
                               message=f'{node} removed from critical section')
    else:
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes,
                               message=f'{node} not found in critical section')


@app.route('/remove_node', methods=['POST'])
def remove_node():
    node = request.form['node']
    if node in nodes:
        nodes.remove(node)
        if node in critical_nodes:
            critical_nodes.remove(node)
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes,
                               message=f'{node} removed from the system')
    else:
        return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes,
                               message=f'{node} not found in the system')


@app.route('/status', methods=['GET'])
def status():
    return render_template('status.html', nodes=nodes, critical_nodes=critical_nodes)


if __name__ == '__main__':
    app.run(debug=True)
