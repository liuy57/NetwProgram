import sys
import socket
import select
import queue
import json


with open('knownhosts.json') as json_file: 
	data = json.load(json_file) 

states = {}
for host in data['hosts']:
	states[host] = True

#print(states)



def client(ip_address,UDP_port_number):
	UDP_IP_ADDRESS = ip_address
	UDP_PORT_NO = UDP_port_number
	Message = "Hello, Server".encode()
	clientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	msg = str(input("Enter your message: "))
	print("You entered: "+ msg)
	msg = msg.encode()
	clientSock.sendto(msg, (UDP_IP_ADDRESS, UDP_PORT_NO))


def server(name,address,start_p,end_p):


	# print(serverIP)
	# inputs = []
	# outputs = []
	# message_queues = {}

	server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	server.setblocking(0)
	server.bind(('localhost', 50000))
	#server.listen(1)
	inputs = [server]
	outputs = []
	message_queues = {}


	# for i in range(serverStartPort,serverEndPort+1):
	# 	server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# 	server.setblocking(0)
	# 	server.bind((socket.gethostname(), i))
	# 	inputs.append(server)


	print(inputs)


	# while inputs:
	# 	readable, writable, exceptional = select.select(inputs, outputs, inputs)
	# 	for s in readable:
	# 		if s is server:
	# 			connection, client_address = s.accept()
	# 			connection.setblocking(0)
	# 			inputs.append(connection)
	# 			message_queues[connection] = Queue.Queue()
	# 		else:
	# 			data = s.recv(1024)
	# 			if data:
	# 				message_queues[s].put(data)
	# 				if s not in outputs:
	# 					outputs.append(s)
	# 			else:
	# 				if s in outputs:
	# 					outputs.remove(s)
	# 				inputs.remove(s)
	# 				s.close()
	# 				del message_queues[s]

	# 	for s in writable:
	# 		try:
	# 			next_msg = message_queues[s].get_nowait()
	# 		except Queue.Empty:
	# 			outputs.remove(s)
	# 		else:
	# 			s.send(next_msg)

	# 	for s in exceptional:
	# 		inputs.remove(s)
	# 		if s in outputs:
	# 			outputs.remove(s)
	# 		s.close()
	# 		del message_queues[s]



if __name__ == '__main__':

	if len(sys.argv) < 2:
		print("ERROR: Please include 1 argument.")
		sys.exit(1)

	argument = sys.argv[1]
	if argument not in data['hosts']:
		sys.exit(1)
	if(argument=='quit' or argument=='ctrl-c'):
		sys.exit(1)
		states[argument] = False
	if(argument=='restart'):
		states[argument] = True


	client(data['hosts'][argument]['ip_address'],data['hosts'][argument]['udp_start_port'])
	for host in data['hosts']:
		if host != argument:
			#print("@"+host)
			server(host,data['hosts'][host]['ip_address'],data['hosts'][host]['udp_start_port'],data['hosts'][host]['udp_end_port'])


