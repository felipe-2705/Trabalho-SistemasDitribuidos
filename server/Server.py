#!/usr/bin/python3

from concurrent import futures
import sys
sys.path.append('../')
from proto import ChatRoom_pb2_grpc as rpc
from proto import ChatRoom_pb2  as chat
import grpc
import time
from threading import Lock
from threading import Thread
from server import ChatRoom as room
import multiprocessing as mp
import os
from State import *
from FingerTable import *

class ChatServer(rpc.ChatSServerServicer):
	def __init__(self):
		self.address      = '0.0.0.0' # Change to get machine ip
		self.Request_port = int(sys.argv[1])
		self.route_table  = FingerTable(self.Request_port)
		self.ChatRooms	  = []	  ## List of Rooms will attach a  note
		self.lock	  = Lock()  ## Lock acess to critical regions
		self.id           = self.route_table.id

		print("Server id : ",self.id)

	# It is missing a method to request the adition of a node in the route_table
	def AddNewNode(self,request,context):
		# Add the new node to its route table
#		print("New node request : ",request.n_id,request.port)
		others = self.route_table.add_node(request.n_id,request.port)
#		print("New table :",self.route_table.servers)
		# Request to some nodes of its table to add the new node
		for node in others:
#			print("Send to ",node)
			channel   = grpc.insecure_channel(self.address + ':' + str(node[1]))
			conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
			conn.AddNewNode(chat.NewNodeReq(n_id=request.n_id,port=request.port))

		return chat.EmptyResponse()


	def FindResponsible(self,request,context):
		print("Try to find",request.roomname)
		resp_node = self.route_table.responsible_node(request.roomname)
		room_name = request.roomname # the name of the room
		resp_serv = resp_node[1][1]  # port of the sever that will/might know who handle

		if resp_node[0] :
			print(resp_serv,"is your guy")
			return chat.FindRResponse(port=resp_serv)
		print(resp_serv,"might knows whos your guy")
		channel   = grpc.insecure_channel(self.address + ':' + str(resp_serv))
		conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
		return conn.FindResponsible(chat.FindRRequest(roomname=room_name))

	# It will write in the log_file
	def CreateChat(self,request,context):
		global state_file

		print("It has begun")
		# Fist - try to descover who will handle the request -----------------------------------------------------------------------
		resp_node = self.route_table.responsible_node(request.roomname)
		print("return : ",resp_node)
		room_name = request.roomname # the id of the room
		resp_serv = resp_node[1][1]  # port of the sever that will/might know who handle
		# If this server dont know who will handle --------------------------------------------------------------------------------
		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			print("I dont know who will handle")
			channel   = grpc.insecure_channel(self.address + ':' + str(resp_serv))
			conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
			result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
			resp_serv = result.port
			print(resp_serv,"will treat")

		# If this server is the one supposed to handle -----------------------------------------------------------------------------
		print(room_name)
		print(resp_serv," ",type(resp_serv))
		if resp_serv == self.Request_port:
			print("I handle")
			if self.Validade_Room(request.roomname,request.password) == None:
				newroom = room.ChatRoom(request.roomname,request.password,state_file.lock) # Chatroom receive
				newroom.Join(request.nickname)

				self.lock.acquire()
				self.ChatRooms.append(newroom)
				self.lock.release()

				print(newroom.Nicknames)
				print('Server: Room ' + request.roomname + ' created ')
#				state_file.stack_log('Server: Room ' + request.roomname + ' created ')
				state_file.stack_log('Created;' + request.nickname + ";" + request.roomname + ";" + request.password)
				res = chat.JoinResponse(state = 'sucess',Port = 0)
				print("Done")

				return res
			else:
				return chat.JoinResponse(state = 'fail',Port = 0)
		# Server knows who will handle --------------------------------------------------------------------------------------------
		print("I know who will handle")
		print("is : ",resp_serv)
		channel = grpc.insecure_channel(self.address + ':' + str(resp_serv))
		conn    = rpc.ChatSServerStub(channel)  ## connection with the responsible server
		result  = conn.CreateChat(chat.CreateChatRequest(roomname=request.roomname,password=request.password,nickname=request.nickname))
		print("Finish him")
		return result

	# It will write in the log file
	def JoinChat(self,request,context):
		global state_file

		# Fist - try to descover who will handle the request -----------------------------------------------------------------------
		resp_node = self.route_table.responsible_node(request.roomname)
		room_name = request.roomname # the name of the room
		resp_serv = resp_node[1][1] # port of the sever that will/might know who handle
		# If this server dont know who will handle --------------------------------------------------------------------------------
		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			channel   = grpc.insecure_channel(self.address + ':' + str(resp_serv))
			conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
			result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
			resp_serv = result.port
		# If this server is the one supposed to handle -----------------------------------------------------------------------------
		if resp_serv == self.Request_port:
			room = self.Validade_Room(request.roomname,request.password)
			if room != None:
				if not room.validate_user(request.nickname):
					room.Join(request.nickname)
#					state_file.stack_log(request.nickname + ' joined ' + request.roomname)
					state_file.stack_log('JoinChat;' + request.nickname + ";" + request.roomname )

					return chat.JoinResponse(state = 'sucess',Port = 0)
			return chat.JoinResponse(state = 'fail',Port = 0)
		# Server knows who will handle --------------------------------------------------------------------------------------------
		channel = grpc.insecure_channel(self.address + ':' + str(resp_serv))
		conn    = rpc.ChatSServerStub(channel)  ## connection with the responsible server
		return conn.JoinChat(chat.JoinChatRequest(roomname=request.roomname,password=request.password,nickname=request.nickname))

	# this method will run in each client to receive all messages
	# send all new messages to clients
	def ReceiveMessage(self,request,context):

		# Fist - try to descover who will handle the request -----------------------------------------------------------------------
		resp_node = self.route_table.responsible_node(request.roomname)
		room_name = request.roomname # the id of the room
		resp_serv = resp_node[1][1] # port of the sever that will/might know who handle
		# If this server dont know who will handle --------------------------------------------------------------------------------
		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			channel   = grpc.insecure_channel(self.address + ':' + str(resp_serv))
			conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
			result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
			resp_serv = result.port
		# If this server is the one supposed to handle -----------------------------------------------------------------------------
		if resp_serv == self.Request_port:
			lastindex = 0
			aux = self.Validade_User(request.roomname,request.nickname)
			if aux != None:
				while True:
					while lastindex < len(aux.Chats):
						n = aux.Chats[lastindex]
						n = chat.Note(roomname=request.roomname, nickname=n['nickname'], message=n['message'])
						lastindex+=1
						yield n
		# Server knows who will handle --------------------------------------------------------------------------------------------
		channel = grpc.insecure_channel(self.address + ':' + str(resp_serv))
		conn    = rpc.ChatSServerStub(channel)  ## connection with the server
		for note in conn.ReceiveMessage(chat.First(roomname=request.roomname,nickname=request.nickname)):
			yield note


	## method to a  client send a message to chatroom
	def SendMessage(self,request,context):
		global state_file

		# Fist - try to descover who will handle the request -----------------------------------------------------------------------
		resp_node = self.route_table.responsible_node(request.roomname)
		room_name = request.roomname # the id of the room
		resp_serv = resp_node[1][1] # port of the sever that will/might know who handle
		# If this server dont know who will handle --------------------------------------------------------------------------------
		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			channel   = grpc.insecure_channel(self.address + ':' + str(resp_serv))
			conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
			result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
			resp_serv = result.port
		# If this server is the one supposed to handle -----------------------------------------------------------------------------
		if resp_serv == self.Request_port:
			aux = self.Validade_User(request.roomname,request.nickname)
			if aux != None:
				aux.Chats.append({'nickname' : request.nickname,'message' : request.message})
				state_file.stack_log('Message;' + request.nickname + ";" + request.roomname + ";" + request.message)
			return chat.EmptyResponse()
		# Server knows who will handle --------------------------------------------------------------------------------------------
		channel = grpc.insecure_channel(self.address + ':' + str(resp_serv))
		conn    = rpc.ChatSServerStub(channel)  ## connection with the server
		return conn.SendMessage(chat.Note(roomname=request.roomname,nickname=request.nickname,message=request.message))

	def Quit(self,request,context):
		global state_file

		# Fist - try to descover who will handle the request -----------------------------------------------------------------------
		resp_node = self.route_table.responsible_node(request.roomname)
		room_name = request.roomname # the id of the room
		resp_serv = resp_node[1][1] # port of the sever that will/might know who handle
		# If this server dont know who will handle --------------------------------------------------------------------------------
		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			channel   = grpc.insecure_channel(self.address + ':' + str(resp_serv))
			conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
			result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
			resp_serv = result.port
		# If this server is the one supposed to handle -----------------------------------------------------------------------------
		if resp_serv == self.Request_port:
			aux = self.Validade_User(request.roomname,request.nickname)
			if aux != None:
				state_file.stack_log('LeftChat;' + request.nickname + ";" + request.roomname )
				aux.Chats.append({'nickname':request.nickname,'message' : request.nickname+' quited chat room;'})
				aux.Nicknames.remove(request.nickname)
				return chat.EmptyResponse()
		# Server knows who will handle --------------------------------------------------------------------------------------------
		channel = grpc.insecure_channel(self.address + ':' + str(resp_serv))
		conn    = rpc.ChatSServerStub(channel)  ## connection with the server
		return conn.Quit(chat.QuitRequest(roomname=request.roomname,nickname=request.nickname))

	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	def Validade_User(self,roomname,user):
		aux = None
		self.lock.acquire()   ### multiple threas may acess this method at same time. though they cant do it currently
		for rooms in self.ChatRooms:
			if rooms.validate_name(roomname) and rooms.validate_user(user):
				aux = rooms
		self.lock.release()
		return aux

	def Validade_Room(self,Roomname,password):
		aux = None
		self.lock.acquire()   ### multiple threas may acess this method at same time. though they cant do it currently
		for rooms in self.ChatRooms:
			if rooms.validate_name(Roomname) and rooms.validate_pass(password):
				aux = rooms
		self.lock.release()
		return aux

	# Will return the id of the server that will store this data
	def room_identificator(self,roomname):
		result = hashlib.md5(roomname.encode())
		ident  = int(result.hexdigest(),16) % self.route_table.m

		return ident

	def getPort(self):
		return self.Request_port

	#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
	def server_snapshot(self):
		global state_file

		time.sleep(30)
		print("Snapshot")
		while True:
			aux   = []
			for i in self.ChatRooms:
				aux.append(i.to_dictionary())
			tm = time.time()
			state = {'time': tm,'server': aux}
			print(state)

			state_file.take_snapshot(state)
			time.sleep(10)

	def recover_state(self):
		global state_file

		snap = state_file.read_snapshot()
		for r in snap['server']:
			newroom = room.ChatRoom(r['room'],r['password'],state_file.lock)
			for u in r['users']:
				newroom.Join(u)
			for m in r['mesgs']:
				newroom.Chats.append(m)
		self.ChatRooms.append(newroom)

		logs = state_file.read_log()
		for command in logs:
			if   command[0] == 'Created':
				newroom = room.ChatRoom(command[2],command[3],state_file.lock)
				newroom.Join(command[1])
				self.ChatRooms.append(newroom)
			elif command[0] == 'JoinChat':
				for ch in self.ChatRooms:
					if ch.Name == command[2]:
						ch.Join(command[1])
			elif command[0] == 'Message':
				for ch in self.ChatRooms:
					if ch.Name == command[2]:
						ch.Chats.append({'nickname' : command[1],'message' : command[3]})
			elif command[0] == 'LeftChat':
				for ch in self.ChatRooms:
					if ch.Name == command[2]:
						ch.Nicknames.remove(command[1])


if __name__ == '__main__':
	chatServer = ChatServer()

	shared_lock = Lock()
	state_file  = State_file(shared_lock,chatServer.route_table.id)
	try:
		chatServer.recover_state()
	except:
		pass
#	Thread(target=state_file.pop_log).start()         # This thread will be responsible to write changes in the log file
#	Thread(target=chatServer.server_snapshot).start() # This thread will be responsible to write the snapshots

	if chatServer.id != 2:
		chatServer.route_table.add_node(2,11912)
		print("Send request")
		channel   = grpc.insecure_channel(chatServer.address + ':' + str(11912))
		conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
		conn.AddNewNode(chat.NewNodeReq(n_id=chatServer.id,port=chatServer.Request_port))

	server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
	rpc.add_ChatSServerServicer_to_server(chatServer,server)
	print('Starting server, Listenning ...')
	server.add_insecure_port('[::]:' + str(chatServer.getPort()))
	server.start()

while True:
	time.sleep(64*64*100)
