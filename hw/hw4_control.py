import os
import sys
import socket
import select
import threading
import queue
import json
import math
from collections import OrderedDict



sensor_dict = {}




class BaseStation:
    def __init__(self, BaseID, x, y, num, links):     
        self.id = BaseID
        self.x = x
        self.y = y
        self.num = num
        self.links = links  


def distance(ax,ay,bx,by):
	dis = math.sqrt(((ax-bx)**2)+((ay-by)**2))
	return dis


def listToString(s):  
    str1 = ""   
    for ele in s:  
        str1 += ele     
    return str1 


def isSensor(base_station,ID):
	for k,v in base_station.items():
		if k==ID:
			return False
	return True


def handling(base_station,reach_list,visited,originID,nextID,destinationID,HopListLength,HopList,message,toSensor):


#	print(visited)

	reach_list = (base_station[nextID]).links
	curr_x = base_station[nextID].x
	curr_y = base_station[nextID].y

	for k,v in sensor_dict.items():
		reach_range = v[0]
		tmp_x = v[1]
		tmp_y = v[2]
		if distance(curr_x,curr_y,tmp_x,tmp_y)<=reach_range:
			reach_list.append(k)

#	visited.add(nextID)

	HopList.append(nextID)
	HopListLength += 1

	if nextID==destinationID:
		print("{}: Message from {} to {} succesfully received.".format(nextID,originID,destinationID))
		sys.stdout.flush()
		return

	if len(visited)==HopListLength:
		print("{}: Message from {} to {} could not be delivered.".format(nextID,originID,destinationID))
		sys.stdout.flush()
		return

	des_x = base_station[destinationID].x
	des_y = base_station[destinationID].y
	
	next_x = base_station[nextID].x
	next_y = base_station[nextID].y
	min_dis = distance(des_x,des_y,next_x,next_y)

	#print(min_dis)

	for node in reach_list:
	#	print(node)
		compare = True
		for i in visited:
			if node==i:
				compare = False
		if compare==True:
			node_x = base_station[node].x
			node_y = base_station[node].y
			if distance(des_x,des_y,node_x,node_y)<min_dis:
				min_dis = distance(des_x,des_y,node_x,node_y)
				nextID = node
			#	print("@@@@@@")
			#	print(nextID)
				visited.add(node)
			#	print(visited)
				if isSensor(base_station,nextID)==False:
					reach_list = (base_station[nextID]).links


	message = "DATAMESSAGE" + originID + " " + destinationID + " " + str(HopListLength) +  " " + listToString(HopList)
	print("{}: Message from {} to {} being forwarded through {}".format(nextID,originID,destinationID,nextID))
	sys.stdout.flush()

	if isSensor(base_station,nextID)==True:
		toSensor = True
		return
	else:
		return handling(base_station,reach_list,visited,originID,nextID,destinationID,HopListLength,HopList,message,False)

		


def recieve_side(control_port,base_station):

	global sensor_dict
	print("recieve_side")
	# print("**************")
	# for k,v in base_station.items():
	# 	print(k)
	# 	print(v.id)
	# 	print(v.x)
	# 	print(v.y)
	# 	print(v.num)
	# 	print(v.links)
	# print("**************")

	# Create a TCP socket
	listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


	# Set the socket to listen on any address, on the specified port
	# bind takes a 2-tuple, not 2 arguments
	listening_socket.bind(('', 50000))
	listening_socket.listen(5)


	# Server loop
	while True:
		# Accept gives us a new socket AND address
		(client_socket, address) = listening_socket.accept()

		# Read data while we can
		while True:
			message = client_socket.recv(1024)

			# Some error checking will use if recv_string == b'':
			if message:
				recv_command = message.decode('utf-8')
				if recv_command.split(" ")[0]=="WHERE":
					print("*********** Control WHERE ***********")
					find_id = (recv_command.split(" ")[1]).strip()
					x_pos = 0
					y_xos = 0
					node_id = ""
					found = False
					for k,v in sensor_dict.items():
						if k==find_id:
							x_pos = v[1]
							y_xos = v[2]

					for k,v in base_station.items():
						if k==find_id:
							x_pos = v.x
							y_xos = v.y

					respond_msg = "THERE " + find_id + " " + str(x_pos) + " " + str(y_xos)
				#	print(respond_msg)
					client_socket.send(respond_msg.encode('utf-8'))

				elif recv_command.split(" ")[0]=="UPDATEPOSITION":
					print("*********** Control UPDATEPOSITION ***********")
					sensor_id = recv_command.split(" ")[1]
					sensor_range = int(recv_command.split(" ")[2])
					sensor_x = int(recv_command.split(" ")[3])
					sensor_y = int(recv_command.split(" ")[4])
					list_tmp = []
					list_tmp.append(sensor_range)
					list_tmp.append(sensor_x)
					list_tmp.append(sensor_y)
					sensor_dict[sensor_id] = list_tmp

					reachable = []

					for k,v in sensor_dict.items():
						if k!=sensor_id:
							if distance(sensor_x,sensor_y,v[1],v[2]) <= sensor_range:
								obj_tmp = k + " " + str(v[1]) + " " + str(v[2]) + " " 
								reachable.append(obj_tmp)

					for k,v in base_station.items():
						if distance(sensor_x,sensor_y,v.x,v.y) <= sensor_range:
							obj_tmp = k + " " + str(v.x) + " " + str(v.y) + " " 
							reachable.append(obj_tmp)

					num_reachable = len(reachable)
					respond_msg =  "REACHABLE " + str(num_reachable) + " " + listToString(reachable) + " "
				#	print(respond_msg)
					client_socket.send(respond_msg.encode('utf-8'))

				elif recv_command.split(" ")[0]=="DATAMESSAGE":
					print("*********** Control DATAMESSAGE ***********")
					originID = recv_command.split(" ")[1]
					nextID = recv_command.split(" ")[2]
					destinationID = recv_command.split(" ")[3]
					HopListLength = int(recv_command.split(" ")[4])

					K = 5
					splt_char = " "
					temp = recv_command.split(" ")[5].split(splt_char) 
					res = splt_char.join(temp[K:]).strip()			
					HopList = res.split(splt_char)
					print("------------------------------")
					print(HopList)
					print("------------------------------")
					toSensor = False
					reach_list = []
					visited = set()
					message = ""
					handling(base_station,reach_list,visited,originID,nextID,destinationID,HopListLength,HopList,message,toSensor)
					if toSensor==True:
						print(message)
						client_socket.send(message.encode('utf-8'))

			else:
				print("Client has closed")
				break

		# Close the connection
		client_socket.close()


def command_side(control_port,base_station):

	while True:
		msg = str(input(""))
		if(msg==""):
			print("ERROR! Please enter valid message!", file=sys.stderr)
			sys.stdout.flush()
			os._exit(1)

		elif msg.split(" ")[0]=='SENDDATA':

			originID = msg.split(" ")[1]
			destinationID = msg.split(" ")[2]

			if originID==destinationID:
				print("ERROR! Could not send message to self!", file=sys.stderr)
				sys.stdout.flush()
				return

			reach_list = []

			print("{}: Sent a new message bound for {}.".format(originID,destinationID))
			sys.stdout.flush()

			if originID=="CONTROL":
				for k,v in base_station.items():
					reach_list.append(k)

				des_x = base_station[destinationID].x
				des_y = base_station[destinationID].y
				star_x = base_station[reach_list[0]].x
				star_y = base_station[reach_list[0]].y				
				min_dis = distance(des_x,des_y,star_x,star_y)
				nextID = reach_list[0]

				for node in reach_list:
					node_x = base_station[node].x
					node_y = base_station[node].y
					if distance(des_x,des_y,node_x,node_y)<min_dis:
						min_dis = distance(des_x,des_y,node_x,node_y)
						nextID = node

			#	print(nextID)
			else:
				reach_list = (base_station[originID]).links
				nextID = originID

			#print(nextID)

			if nextID==destinationID:
				print("{}: Sent a new message directly to {}.".format(originID,destinationID))
				sys.stdout.flush()

			HopListLength = 0
			HopList = []
			visited = set()
			message = "DATAMESSAGE" + originID + " " + destinationID + " " + str(HopListLength) +  " " + listToString(HopList)

			handling(base_station,reach_list,visited,originID,nextID,destinationID,HopListLength,HopList,message)

		elif msg.split(" ")[0]=='QUIT':
			os._exit(1)
		else:
			print("ERROR! Not valid command!", file=sys.stderr)
			sys.stdout.flush()		
			os._exit(1)




if __name__ == '__main__':

	if len(sys.argv) != 3:
		print("Error, correct usage is {} [control port] [base station file]".format(sys.argv[0]))
		sys.stdout.flush()
		sys.exit(1)

	control_port = int(sys.argv[1])
	base_station_file = sys.argv[2]

	base_station = {}
	with open(base_station_file, 'r') as f:
		for line in f:
			BaseID = line.split(" ")[0]
			x = int(line.split(" ")[1])
			y = int(line.split(" ")[2])
			num = int(line.split(" ")[3])
			K = 4
			splt_char = " "
			temp = line.split(splt_char) 
			res = splt_char.join(temp[K:]).strip()			
			links = res.split(splt_char)
			key = BaseID
			val = BaseStation(BaseID,x,y,num,links)
			base_station[key] = val

	# make two thread, one for input and send message, the other for recieving
	thread_one = threading.Thread(target=command_side, args=(control_port,base_station,))
	thread_two = threading.Thread(target=recieve_side, args=(control_port,base_station,))     

	# start the recieve side first and close last
	thread_two.start()
	thread_one.start()

	thread_one.join()
	thread_two.join()



	# my_hostname = socket.gethostname() # Gets my host name
	# my_address = socket.gethostbyname(my_hostname) # Gets my IP address from my hostname
	# local_address = my_address


	# server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# server.setblocking(0)
	# server.bind(('', 50000))
	# server.listen(5)
	# inputs = [server]
	# outputs = []
	# message_queues = {}

	# while inputs:
	# 	readable, writable, exceptional = select.select(inputs, outputs, inputs)
	# 	for s in readable:
	# 		if s is server:
	# 			connection, client_address = s.accept()
	# 			connection.setblocking(0)
	# 			inputs.append(connection)
	# 			message_queues[connection] = queue.Queue()
	# 		else:
	# 			data = s.recv(1024)
	# 			print(data)
	# 			print(type(data))



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
	# 		except queue.Empty:
	# 			outputs.remove(s)
	# 		else:
	# 			s.send(next_msg)

	# 	for s in exceptional:
	# 		inputs.remove(s)
	# 		if s in outputs:
	# 			outputs.remove(s)
	# 		s.close()
	# 		del message_queues[s]	


	# 	socket.close()
