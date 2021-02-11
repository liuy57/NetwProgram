#!/usr/bin/env python3

from concurrent import futures
import sys  # For sys.argv, sys.exit()
import socket  # for gethostbyname()
import os
import select
import logging
import grpc

import csci4220_hw3_pb2
import csci4220_hw3_pb2_grpc


global N
N = 4
bucket = {}
local_node = 0
local_port = 0
local_address = ""
local_key = 2000
local_value = ""
bucket_max = 0
already_quit = False




# function to calculate distance
def XOR(a,b):
	x = bin(a)[2:]
	y = bin(b)[2:]
	z = int(x,2) ^ int(y,2)
	return z


# function to locate bucket position
def locateBucket(a,b):
	distance = XOR(a,b)
	if distance<=0:
		return -1
	elif distance>=1 and distance<2:
		return 0
	elif distance>=2 and distance<4:
		return 1
	elif distance>=4 and distance<8:
		return 2
	else:
		return 3


# node object
class nodeObj:
	def __init__(self, ID, port, address):      
		self.id = ID 
		self.port = port
		self.address = address



# server class
class KadImplServicer(csci4220_hw3_pb2_grpc.KadImplServicer):
	"""Provides methods that implement functionality of KadImplServicer server."""

	def FindNode(self, request, context):
		
		global bucket
		
		# Findnode function for bootstrap
		if request.idkey==request.node.id:
			index = locateBucket(local_node,request.node.id)
			if index!=-1:
				if index not in bucket:
					tmp = []
					tmp.append(nodeObj(request.node.id,request.node.port,request.node.address))
					bucket[index] = tmp
				else:
					adding = True
					for k,v in bucket.items():
						for i in range(0,len(v)):
							if v[i].id==request.node.id:
								adding = False
					if adding==True:
						n = len(bucket[index])
						tmp = bucket[index]
						if n==bucket_max:
							tmp.pop()
						tmp.insert(0,nodeObj(request.node.id,request.node.port,request.node.address))
						bucket[index] = tmp
					
			# add all nodes to a list and sort
			all_nodes = []
			for k,v in bucket.items():
				for j in range(len(v)):
					if v[j].id!=request.node.id:
						all_nodes.append(v[j])

			ordered_nodes = sorted(all_nodes, key=lambda x : XOR(x.id,request.node.id))
			node_tmp = csci4220_hw3_pb2.Node(id=local_node,port=local_port,address=local_address)
			ret = []			
			
			# update bucket
			i = 0
			for node in ordered_nodes:
				i += 1
				if i>bucket_max:
					break
				else:
					if node.id==0:
						tmp = csci4220_hw3_pb2.Node(id=1000,port=node.port,address=node.address)
						ret.append(tmp)
					else:
						tmp = csci4220_hw3_pb2.Node(id=node.id,port=node.port,address=node.address)
						ret.append(tmp)

			print("Serving FindNode(" + str(request.node.id) + ") request for " + str(request.idkey))
			sys.stdout.flush()
			return csci4220_hw3_pb2.NodeList(responding_node=node_tmp,nodes=ret)


		# Findnode function for find node 
		else:
			index = locateBucket(local_node,request.node.id)
			if index!=-1:
				if index not in bucket:
					tmp = []
					tmp.append(nodeObj(request.node.id,request.node.port,request.node.address))
					bucket[index] = tmp
				else:
					adding = True
					for k,v in bucket.items():
						for i in range(0,len(v)):
							if v[i].id==request.node.id:
								adding = False
					if adding==True:					
						n = len(bucket[index])
						tmp = bucket[index]
						if n==bucket_max:
							tmp.pop()
						tmp.insert(0,nodeObj(request.node.id,request.node.port,request.node.address))
						bucket[index] = tmp


			all_nodes = []
			for k,v in bucket.items():
				for j in range(len(v)):
					all_nodes.append(v[j])

			ordered_nodes = sorted(all_nodes, key=lambda x : XOR(x.id,request.node.id))

			node_tmp = csci4220_hw3_pb2.Node(id=local_node,port=local_port,address=local_address)
			ret = []

			# update bucket
			for node in ordered_nodes:
				if node.id!=request.idkey:
					if node.id==0:
						tmp = csci4220_hw3_pb2.Node(id=1000,port=node.port,address=node.address)
						ret.append(tmp)
					else:
						tmp = csci4220_hw3_pb2.Node(id=node.id,port=node.port,address=node.address)
						ret.append(tmp)

			print("Serving FindNode(" + str(request.node.id) + ") request for " + str(request.idkey))
			sys.stdout.flush()
			return csci4220_hw3_pb2.NodeList(responding_node=node_tmp,nodes=ret)
		


	def FindValue(self, request, context):

		global bucket

		# delete same nodes
		for k,v in list(bucket.items()):
			for i in range(0,len(v)):
				if v[i].id==local_node:
					if len(v)==1:
						del bucket[k]
					else:
						v.remove(i)


		print("Serving FindKey(" + str(request.idkey) + ") request for " + str(request.node.id))
		sys.stdout.flush()

		# if found the key in server node, return the key directly
		if request.idkey==local_key:
			r_node = csci4220_hw3_pb2.Node(id=local_node,port=local_port,address=local_address)
			mode = True
			key_value = csci4220_hw3_pb2.KeyValue(node=r_node,key=local_key,value=local_value)
			return csci4220_hw3_pb2.KV_Node_Wrapper(responding_node=r_node,mode_kv=mode,kv=key_value,nodes=[])


		# if not found, return a k-near list of nodes
		else:
			mode = False

			index = locateBucket(local_node,request.node.id)
			if index!=-1:
				if index not in bucket:
					tmp = []
					tmp.append(nodeObj(request.node.id,request.node.port,request.node.address))
					bucket[index] = tmp
				else:
					adding = True
					n = len(bucket[index])
					for i in range(0,n):
						if bucket[index][i].id==request.node.id:
							adding = False
							break
					if adding==True:
						if n==bucket_max:
							tmp = bucket[index]
							tmp.pop()
							tmp.insert(0,nodeObj(request.node.id,request.node.port,request.node.address))
							bucket[index] = tmp


			all_nodes = []
			for k,v in bucket.items():
				for j in range(len(v)):
					all_nodes.append(v[j])

			ordered_nodes = sorted(all_nodes, key=lambda x : XOR(x.id,request.node.id))

			node_tmp = csci4220_hw3_pb2.Node(id=local_node,port=local_port,address=local_address)
			ret = []

			for node in ordered_nodes:
				if node.id==0:
					tmp = csci4220_hw3_pb2.Node(id=1000,port=node.port,address=node.address)
				else:
					tmp = csci4220_hw3_pb2.Node(id=node.id,port=node.port,address=node.address)
				ret.append(tmp)

			r_node = csci4220_hw3_pb2.Node(id=local_node,port=local_port,address=local_address)
			key_value = csci4220_hw3_pb2.KeyValue(node=r_node,key=local_key,value=local_value)
			return csci4220_hw3_pb2.KV_Node_Wrapper(responding_node=r_node,mode_kv=mode,kv=key_value,nodes=ret)
		

	def Store(self, request, context):

		global bucket
		global local_key
		global local_value

		# store nodes directly at server node
		local_key = request.key
		local_value = request.value

		print('Storing key {} value "{}"'.format(request.key,request.value))
		sys.stdout.flush()

		if request.node.id==1000:
			request.node.id = 0
		index = locateBucket(local_node,request.node.id)
		if index!=-1:
			if index not in bucket:
				tmp = []
				tmp.append(nodeObj(request.node.id,request.node.port,request.node.address))
				bucket[index] = tmp
			else:
				n = len(bucket[index])
				if n==bucket_max:
					tmp = bucket[index]
					tmp.pop()
					tmp.insert(0,nodeObj(request.node.id,request.node.port,request.node.address))
					bucket[index] = tmp


		tmp = csci4220_hw3_pb2.Node(id=local_node,port=local_port,address=local_address)
		return csci4220_hw3_pb2.IDKey(node=tmp,idkey=request.key)


	def Quit(self, request, context):

		global bucket
		Found = False

		if request.node.id==1000:
			request.node.id = 0

		# loop over to find client node and delete it from bucket
		for k,v in list(bucket.items()):
			mark = -1
			for i in range(0,len(v)):
				if v[i].id==request.idkey:
					mark = i
					if len(v)>1:
						Found = True
						print("Evicting quitting node {} from bucket {}".format(request.idkey,k))
						sys.stdout.flush()	
			if mark!=-1 and Found==True:
				v.remove(mark)

											
		for k,v in list(bucket.items()):
			for i in range(0,len(v)):
				if v[i].id==request.idkey:
					if len(v)==1:
						Found = True
						del bucket[k]
						print("Evicting quitting node {} from bucket {}".format(request.idkey,k))
						sys.stdout.flush()	
					
		if Found==False:
			print("No record of quitting node {} in k-buckets.".format(request.node.id))
			sys.stdout.flush()

		r_node = csci4220_hw3_pb2.Node(id=local_node,port=local_port,address=local_address)
		return csci4220_hw3_pb2.IDKey(node=r_node,idkey=local_node)






# function of client side
def bootStrap(stub,remote_host,remote_port):

	global bucket_max

	# locate other side send connection
	node_tmp = csci4220_hw3_pb2.Node(id=local_node,port=local_port,address=local_address)
	idKey = csci4220_hw3_pb2.IDKey(node=node_tmp,idkey=local_node)
	nodeList = stub.FindNode(idKey)


	to_bucket = []
	to_bucket.append(nodeList.responding_node)
	for node in nodeList.nodes:
		to_bucket.append(node)


	# update bucket
	for x in to_bucket:
		if x.id==1000:
			x.id = 0
		add = True
		for item in bucket.items():
			for node in item[1]:
				if x.id==node.id:
					add = False
		if add==True:

			index = locateBucket(local_node,x.id)

			if index!=-1:
				if index not in bucket:
					tmp = []
					obj = nodeObj(x.id,x.port,x.address)
					tmp.append(obj)
					bucket[index] = tmp
				else:
					n = len(bucket[index])
					tmp = bucket[index]
					if n==bucket_max:
						l = tmp[-1]
						tmp[-1] = tmp[0]
						tmp[0] = l
						tmp.pop()
					obj = nodeObj(x.id,x.port,x.address)
					tmp.append(obj)					
					bucket[index] = tmp

	# outprint
	print("After BOOTSTRAP(" + str(remote_host) + "), k_buckets now look like:")
	sys.stdout.flush()
	for i in range(0,N):
		tmp = str(i)+":"
		for k,v in bucket.items():
			if k==i and len(v)!=0:
				for m in v:
					tmp += " "
					tmp += str(m.id)
					tmp += ":"
					tmp += str(m.port)
		print(tmp)
		sys.stdout.flush()



def findingNode(find_node_id):

	visited = []
	Found = False

	print("Before FIND_NODE command, k-buckets are:")
	sys.stdout.flush()
	for i in range(0,N):
		tmp = str(i)+":"
		for k,v in bucket.items():
			if k==i and len(v)!=0:
				for m in v:
					tmp += " "
					tmp += str(m.id)
					tmp += ":"
					tmp += str(m.port)
		print(tmp)
		sys.stdout.flush()


	all_nodes = []
	for k,v in bucket.items():
		for j in range(len(v)):
			if v[j].id==find_node_id:
				Found = True
				index = locateBucket(find_node_id,local_node)
				tmp = bucket[index]
				x = v[j]
				tmp.remove(x)
				tmp.insert(0, x)
				print("Found destination id " + str(find_node_id))
				sys.stdout.flush()
				print("After FIND_NODE command, k-buckets are:")
				sys.stdout.flush()
				for i in range(0,N):
					tmp = str(i)+":"
					for k,v in bucket.items():
						if k==i and len(v)!=0:
							for m in v:
								tmp += " "
								tmp += str(m.id)
								tmp += ":"
								tmp += str(m.port)
					print(tmp)
					sys.stdout.flush()
				return
			else:
				all_nodes.append(v[j])

	ordered_nodes = sorted(all_nodes, key=lambda x : XOR(x.id,find_node_id))

	S = []
	S_prime = []
	if len(ordered_nodes)<bucket_max:
		S = ordered_nodes
	else:
		for i in range(0,bucket_max):
			S.append(ordered_nodes[i])


	for x in S:
		add = True
		for v_node in visited:
			if x==v_node:
				add = False
		if add==True:
			S_prime.append(x)


	for search_node in S_prime:

		if search_node.id==find_node_id:
			Found = True
			print("Found destination id " + str(find_node_id))
			break

		visited.append(search_node.id)
		remote_host = search_node.id
		remote_port = int(search_node.port)
		remote_addr = search_node.address
		with grpc.insecure_channel(remote_addr + ':' + str(remote_port)) as channel:
			stub = csci4220_hw3_pb2_grpc.KadImplStub(channel)
			node_tmp = csci4220_hw3_pb2.Node(id=find_node_id,port=0,address="")
			idKey = csci4220_hw3_pb2.IDKey(node=node_tmp,idkey=local_node)
			nodeList = stub.FindNode(idKey)

			R = []
			for node in nodeList.nodes:
				R.append(node)

		mr_used = search_node
		mr_index = locateBucket(local_node,mr_used.id)

		for x in R:
			if x.id==1000:
				x.id = 0	
			if x.id==find_node_id:
				Found = True
				print("Found destination id " + str(find_node_id))						
			index = locateBucket(local_node,x.id)
			update = True
			for k,v in bucket.items():
				if k==index:
					for i in range(0,len(v)):
						if v[i].id==mr_used.id or v[i].id==local_node:
							update==False
						for j in range(0,len(v)):
							if v[i].id==v[j].id:
								update==False

			if update==True:
				mr_used = x
				if index not in bucket:
					tmp = []
					tmp.append(x)
					bucket[index] = tmp
				else:
					tmp = bucket[index]
					tmp.append(x)
					n = len(tmp)
					if n>bucket_max:
						tmp.pop(0)
						bucket[index] = tmp				

		if mr_index in bucket.values():
			bucket[mr_index].remove(mr_used)
			bucket[mr_index].insert(0,mr_used)

		channel.close()

	print("After FIND_NODE command, k-buckets are:")
	sys.stdout.flush()
	for i in range(0,N):
		tmp = str(i)+":"
		for k,v in bucket.items():
			if k==i and len(v)!=0:
				for m in v:
					tmp += " "
					tmp += str(m.id)
					tmp += ":"
					tmp += str(m.port)
		print(tmp)
		sys.stdout.flush()

	if Found==False:
		print("Could not find destination id " + str(find_node_id))
		sys.stdout.flush()



def findingValue(find_key):
	visited = []
	Found = False

	print("Before FIND_VALUE command, k-buckets are:")
	sys.stdout.flush()
	for i in range(0,N):
		tmp = str(i)+":"
		for k,v in bucket.items():
			if k==i and len(v)!=0:
				for m in v:
					tmp += " "
					tmp += str(m.id)
					tmp += ":"
					tmp += str(m.port)
		print(tmp)
		sys.stdout.flush()


	all_nodes = []
	for k,v in bucket.items():
		for j in range(len(v)):
			if v[j].id!=local_node:
				all_nodes.append(v[j])

	ordered_nodes = sorted(all_nodes, key=lambda x : XOR(x.id,local_node))

	S = []
	S_prime = []
	if len(ordered_nodes)<bucket_max:
		S = ordered_nodes
	else:
		for i in range(0,bucket_max):
			S.append(ordered_nodes[i])

	for x in S:
		add = True
		for v_node in visited:
			if x==v_node:
				add = False
		if add==True:
			S_prime.append(x)

	for search_node in S_prime:

		visited.append(search_node.id)
		remote_host = search_node.id
		remote_port = int(search_node.port)
		remote_addr = search_node.address
		with grpc.insecure_channel(remote_addr + ':' + str(remote_port)) as channel:
			stub = csci4220_hw3_pb2_grpc.KadImplStub(channel)
			node_tmp = csci4220_hw3_pb2.Node(id=local_node,port=local_port,address=local_address)
			idKey = csci4220_hw3_pb2.IDKey(node=node_tmp,idkey=find_key)
			ret = stub.FindValue(idKey)

			if ret.mode_kv==True:
				Found = True

				tmp_p = '"'+ret.kv.value+'"'
				print("Found value ""{}"" for key {}".format(tmp_p,find_key))


				mr_used = ret.responding_node
				mr_index = locateBucket(local_node,mr_used.id)

				if mr_index not in bucket:
					tmp = []
					tmp.append(mr_used)
					bucket[mr_index] = tmp
				else:
					adding = True
					for y in bucket[mr_index]:
						if y.id==mr_used.id and len(bucket[mr_index])==1:
							adding = False
						elif y.id==mr_used.id and len(bucket[mr_index])==bucket_max and bucket[mr_index][-1].id==mr_used.id:
							adding = False
					if adding==True:
						tmp = bucket[mr_index]
						tmp.pop(0)
						tmp.append(mr_used)
						bucket[mr_index] = tmp				

				break


			elif ret.mode_kv==False:

				R = []
				for node in ret.nodes:
					R.append(node)

				mr_used = search_node
				mr_index = locateBucket(local_node,mr_used.id)

				for x in R:
					if x.id==1000:
						x.id = 0	
					if x.id==find_key:
						Found = True
						remote_host = x.id
						remote_port = int(x.port)
						remote_addr = x.address
						with grpc.insecure_channel(remote_addr + ':' + str(remote_port)) as channel:
							stub = csci4220_hw3_pb2_grpc.KadImplStub(channel)
							node_tmp = csci4220_hw3_pb2.Node(id=local_node,port=local_port,address=local_address)
							idKey = csci4220_hw3_pb2.IDKey(node=node_tmp,idkey=find_key)
							result = stub.FindValue(idKey)						

						tmp_p = '"'+result.kv.value+'"'
						print("Found value ""{}"" for key {}".format(tmp_p,find_key))						
					index = locateBucket(local_node,x.id)
					update = True
					for k,v in bucket.items():
						if k==index:
							for i in range(0,len(v)):
								if v[i].id==mr_used.id or v[i].id==local_node:
									update==False

					if update==True:
						if index not in bucket:
							tmp = []
							tmp.append(x)
							bucket[index] = tmp
						else:
							adding = True
							for y in bucket[index]:
								if y.id==mr_used.id:
									adding = False
							if adding==True:
								tmp = bucket[index]
								n = len(tmp)
								if n<bucket_max:
									tmp.insert(0,x)
								else:
									tmp.insert(0,x)
									tmp.pop()
							#	print(tmp)
								bucket[index] = tmp				

				if mr_index in bucket.values():
					bucket[mr_index].remove(mr_used)
					bucket[mr_index].insert(0,mr_used)

		channel.close()

	if Found==False:
		print("Could not find key " + str(find_key))
		sys.stdout.flush()


	print("After FIND_VALUE command, k-buckets are:")
	sys.stdout.flush()
	for i in range(0,N):
		tmp = str(i)+":"
		for k,v in bucket.items():
			if k==i and len(v)!=0:
				for m in v:
					tmp += " "
					tmp += str(m.id)
					tmp += ":"
					tmp += str(m.port)
		print(tmp)
		sys.stdout.flush()






if __name__ == '__main__':

	if len(sys.argv) != 4:
		print("Error, correct usage is {} [my id] [my port] [k]".format(sys.argv[0]))
		sys.stdout.flush()
		sys.exit(-1)

	local_id = int(sys.argv[1])
	my_port = str(int(sys.argv[2])) # add_insecure_port() will want a string
	k = int(sys.argv[3])

	local_node = local_id
	local_port = int(sys.argv[2])
	bucket_max = k

	my_hostname = socket.gethostname() # Gets my host name
	my_address = socket.gethostbyname(my_hostname) # Gets my IP address from my hostname
	local_address = my_address

	logging.basicConfig()


    # start serverside and then client side begin to revieve command
	server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
	csci4220_hw3_pb2_grpc.add_KadImplServicer_to_server(KadImplServicer(), server)


	str_my_port = '[::]:' + my_port
	server.add_insecure_port(str_my_port)
	server.start()


	while True:
		msg = str(input(""))
		if(msg==""):
			print("ERROR! Please enter valid message!", file=sys.stderr)
			sys.stdout.flush()
			os._exit(1)

		elif msg.split(" ")[0]=='BOOTSTRAP':
			remote_host = ""
			tmp = msg.split(" ")[1]
			if tmp=="peer00":
				remote_host = 0
			elif tmp[0:5]=="peer0":
				remote_host = int(tmp.split("0")[1])
			else:
				remote_host = int(tmp.split("r")[1])
			remote_port = int(msg.split(" ")[2])

			with grpc.insecure_channel(tmp + ':' + str(remote_port)) as channel:


				stub = csci4220_hw3_pb2_grpc.KadImplStub(channel)
				bootStrap(stub,remote_host,remote_port)
			channel.close()


		elif msg.split(" ")[0]=='FIND_NODE':
			node = int(msg.split(" ")[1])
			if node==local_id:
				print("Found destination id " + str(node))
				sys.stdout.flush()
			else:
				findingNode(node)

		elif msg.split(" ")[0]=='FIND_VALUE':

			key = int(msg.split(" ")[1])
			if key==local_key:

				print("Before FIND_VALUE command, k-buckets are:")
				sys.stdout.flush()
				for i in range(0,N):
					tmp = str(i)+":"
					for k,v in bucket.items():
						if k==i and len(v)!=0:
							for m in v:
								tmp += " "
								tmp += str(m.id)
								tmp += ":"
								tmp += str(m.port)
								
					print(tmp)
					sys.stdout.flush()

				tmp_p = '"'+local_value+'"'
				print("Found data ""{}"" for key {}".format(tmp_p, local_key))
				sys.stdout.flush()

				print("After FIND_VALUE command, k-buckets are:")
				sys.stdout.flush()
				for i in range(0,N):
					tmp = str(i)+":"
					for k,v in bucket.items():
						if k==i and len(v)!=0:
							for m in v:
								tmp += " "
								tmp += str(m.id)
								tmp += ":"
								tmp += str(m.port)
								
					print(tmp)
					sys.stdout.flush()

			else:
				findingValue(key)
		
		elif msg.split(" ")[0]=='STORE':

			key = int(msg.split(" ")[1])
			value = msg.split(" ")[2]
			min_distrance = XOR(key,local_id)
			target = nodeObj(local_id,my_port,my_address)
			for k,v in bucket.items():
				for i in range(0,len(v)):
					if XOR(v[i].id,key)<=min_distrance:
						min_distrance = XOR(v[i].id,key)
						target = v[i]

			tmp_id = target.id

			if target.id==local_id:
				local_key = key
				local_value = value
				print("Storing key " + str(key) + " at node " + str(local_id))
				sys.stdout.flush()
			else:
				if target.id==0:
					tmp_id = 1000

				node = csci4220_hw3_pb2.Node(id=tmp_id,port=target.port,address=target.address)
				ky = csci4220_hw3_pb2.KeyValue(node=node,key=key,value=value)
				with grpc.insecure_channel(target.address + ':' + str(target.port)) as channel:
					stub = csci4220_hw3_pb2_grpc.KadImplStub(channel)
					stub.Store(ky)
				print("Storing key " + str(key) + " at node " + str(target.id))
				sys.stdout.flush()
				channel.close()


		elif msg.split(" ")[0]=='QUIT':

			if already_quit==False:
				for k,v in list(bucket.items()):
					for i in range(0,len(v)):
						if v[i].id!=local_node:
							re_id = v[i].id
							if v[i].id==0:
								re_id = 1000
							print("Letting " + str(v[i].id) + " know I'm quitting.")
							sys.stdout.flush()	
							node = csci4220_hw3_pb2.Node(id=re_id,port=v[i].port,address=v[i].address)
							id_key = csci4220_hw3_pb2.IDKey(node=node,idkey=local_node)
							with grpc.insecure_channel(v[i].address + ':' + str(v[i].port)) as channel:
								stub = csci4220_hw3_pb2_grpc.KadImplStub(channel)
								stub.Quit(id_key)
							channel.close()

				for k,v in list(bucket.items()):
					del bucket[k]

				print("Shut down node " + str(local_node))
				sys.stdout.flush()
			already_quit = True

		else:
			print("ERROR! Not valid command!", file=sys.stderr)
			sys.stdout.flush()		
			os._exit(1)

	server.wait_for_termination()


