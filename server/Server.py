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

		print("Server id : ",self.route_table.id)

	def FindResponsible(self,request,context):
		resp_node = self.route_table.responsible_node(request.roomname)
		room_name = resp_node[1][0] # the name of the room
		resp_serv = resp_node[1][1] # port of the sever that will/might know who handle

		if resp_node[0] :
			return chat.FindRResponse(port=resp_serv)
		channel   = grpc.insecure_channel(self.address + ':' + str(resp_serv))
		conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
		return conn.FindResponsible(chat.FindRRequest(roomname=room_name))


	# It will write in the log file
	def JoinChat(self,request,context):
		global state_file

		# Fist - try to descover who will handle the request -----------------------------------------------------------------------
		resp_node = self.route_table.responsible_node(request.roomname)
		room_name = resp_node[1][0] # the name of the room
		resp_serv = resp_node[1][1] # port of the sever that will/might know who handle
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
		# If this server dont know who will handle --------------------------------------------------------------------------------
		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			channel   = grpc.insecure_channel(self.address + ':' + str(resp_serv))
			conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
			result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
			resp_serv = result.port
		# Server knows who will handle --------------------------------------------------------------------------------------------
		channel = grpc.insecure_channel(self.address + ':' + str(resp_serv))
		conn    = rpc.ChatSServerStub(channel)  ## connection with the responsible server
		return conn.JoinChat(chat.JoinChatRequest(roomname=request.roomname,password=request.password,nickname=request.nickname))


	# It will write in the log_file
	def CreateChat(self,request,context):
		global state_file

		print("It has begun")
		# Fist - try to descover who will handle the request -----------------------------------------------------------------------
		resp_node = self.route_table.responsible_node(request.roomname)
		print(resp_node)
		room_name = resp_node[1][0] # the id of the room
		resp_serv = resp_node[1][1] # port of the sever that will/might know who handle
		# If this server is the one supposed to handle -----------------------------------------------------------------------------
		if resp_serv == self.Request_port:
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

				return chat.JoinResponse(state = 'sucess',Port = 0)
			else:
				return chat.JoinResponse(state = 'fail',Port = 0)
		# If this server dont know who will handle --------------------------------------------------------------------------------
		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			channel   = grpc.insecure_channel(self.address + ':' + str(resp_serv))
			conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
			result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
			resp_serv = result.port
		# Server knows who will handle --------------------------------------------------------------------------------------------
		channel = grpc.insecure_channel(self.address + ':' + str(resp_serv))
		conn    = rpc.ChatSServerStub(channel)  ## connection with the responsible server
		return conn.CreateChat(chat.CreateChatRequest(roomname=request.roomname,password=request.password,nickname=request.nickname))


	# this method will run in each client to receive all messages
	# send all new messages to clients
	def ReceiveMessage(self,request,context):

		# Fist - try to descover who will handle the request -----------------------------------------------------------------------
		resp_node = self.route_table.responsible_node(request.roomname)
		room_name = resp_node[1][0] # the id of the room
		resp_serv = resp_node[1][1] # port of the sever that will/might know who handle
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
		# If this server dont know who will handle --------------------------------------------------------------------------------
		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			channel   = grpc.insecure_channel(self.address + ':' + str(resp_serv))
			conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
			result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
			resp_serv = result.port
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
		room_name = resp_node[1][0] # the id of the room
		resp_serv = resp_node[1][1] # port of the sever that will/might know who handle
		# If this server is the one supposed to handle -----------------------------------------------------------------------------
		if resp_serv == self.Request_port:
			aux = self.Validade_User(request.roomname,request.nickname) 
			if aux != None:
				aux.Chats.append({'nickname' : request.nickname,'message' : request.message})
#				aux.Chats.append(request)
#				state_file.stack_log('ChatRoom ' + request.roomname + ': Message received from: ' + request.nickname)
				state_file.stack_log('Message;' + request.nickname + ";" + request.roomname + ";" + request.message)
			return chat.EmptyResponse()
		# If this server dont know who will handle --------------------------------------------------------------------------------
		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			channel   = grpc.insecure_channel(self.address + ':' + str(resp_serv))
			conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
			result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
			resp_serv = result.port
		# Server knows who will handle --------------------------------------------------------------------------------------------
		channel = grpc.insecure_channel(self.address + ':' + str(resp_serv))
		conn    = rpc.ChatSServerStub(channel)  ## connection with the server
		return conn.SendMessage(chat.Note(roomname=request.roomname,nickname=request.nickname,message=request.message))

	def Quit(self,request,context):
		aux = self.Validade_User(request.roomname,request.nickname) 
		if aux != None:
			aux.Nicknames.remove(request.nickname)

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
		ident  = int(result.hexdigest(),16) % 5

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

	
if __name__ == '__main__':
	chatServer = ChatServer()

	shared_lock = Lock()
	state_file  = State_file(shared_lock,chatServer.route_table.id)
	chatServer.recover_state()
	Thread(target=state_file.pop_log).start()         # This thread will be responsible to write changes in the log file
	Thread(target=chatServer.server_snapshot).start() # This thread will be responsible to write the snapshots

	server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
	rpc.add_ChatSServerServicer_to_server(chatServer,server)
	print('Starting server, Listenning ...')
	server.add_insecure_port('[::]:' + str(chatServer.getPort()))
	server.start()

while True:
	time.sleep(64*64*100)
