# app.py
from flask import Flask, request, render_template
import socket
import sys

app = Flask(__name__)

nodes = []  # list of all nodes in the distributed system
critical_nodes = []  # list of nodes currently in the critical section

# Declaring Main socket to create Master Node
sock = socket.socket()


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
