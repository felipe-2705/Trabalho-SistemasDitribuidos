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
import hashlib

class ChatServer(rpc.ChatSServerServicer):
	def __init__(self):
		self.address      = '0.0.0.0' # Change to get machine ip
		self.Request_port = int(sys.argv[1])
#		self.Request_port = 11912   ## Port that will receive join and create Request ## This will be used in the server identification
#		self.route_table  = []

		self.ChatRooms	  = []	  ## List of Rooms will attach a  note
		self.lock	  = Lock()  ## Lock acess to critical regions
		self.id           = self.Request_port - 11910

		print("Server id : ",self.id)

	# It will write in the log file
	def JoinChat(self,request,context):
		global state_file

		print(request.roomname)
		r_id = self.room_identificator(request.roomname)
		print("Id : ",r_id)
		if r_id == self.id :
			room = self.Validade_Room(request.roomname,request.password)
			if room != None:
				if not room.validate_user(request.nickname):
					room.Join(request.nickname)
					state_file.stack_log(request.nickname + ' joined ' + request.roomname)

					return chat.JoinResponse(state = 'sucess',Port = 0)
			return chat.JoinResponse(state = 'fail',Port = 0)
		else:
			channel = grpc.insecure_channel(self.address + ':' + str(r_id + 11910))
			conn    = rpc.ChatSServerStub(channel)  ## connection with the server

			print('Joining ',r_id + 11910)

			return conn.JoinChat(chat.JoinChatRequest(roomname=request.roomname,password=request.password,nickname=request.nickname))

	# It will write in the log_file
	def CreateChat(self,request,context):
		global state_file

		print(request.roomname)
		r_id = self.room_identificator(request.roomname)
		print("Id : ",r_id)
		if r_id == self.id :
			if self.Validade_Room(request.roomname,request.password) == None:
				newroom = room.ChatRoom(request.roomname,request.password,state_file.lock) # Chatroom receive
				newroom.Join(request.nickname)

				self.lock.acquire()
				self.ChatRooms.append(newroom)
				self.lock.release()

				print(newroom.Nicknames)
				print('Server: Room ' + request.roomname + ' created ')
				state_file.stack_log('Server: Room ' + request.roomname + ' created ')
				return chat.JoinResponse(state = 'sucess',Port = 0)
			else:
				return chat.JoinResponse(state = 'fail',Port = 0)
		else :
			channel = grpc.insecure_channel(self.address + ':' + str(r_id + 11910))
			conn    = rpc.ChatSServerStub(channel)  ## connection with the server

			print('Connecting to ',r_id + 11910)

			return conn.CreateChat(chat.CreateChatRequest(roomname=request.roomname,password=request.password,nickname=request.nickname))

	# this method will run in each client to receive all messages
	# send all new messages to clients
	def ReceiveMessage(self,request,context):
		print(request.roomname)
		r_id = self.room_identificator(request.roomname)
		print("Recv : Id : ",r_id)

		if r_id == self.id:
			lastindex = 0
			aux = self.Validade_User(request.roomname,request.nickname) 
			if aux != None:
				while True:
					while lastindex < len(aux.Chats):
						n = aux.Chats[lastindex]
						n = chat.Note(roomname=request.roomname, nickname=n['nickname'], message=n['message'])
						lastindex+=1
						yield n
		else:
			channel = grpc.insecure_channel(self.address + ':' + str(r_id + 11910))
			conn    = rpc.ChatSServerStub(channel)  ## connection with the server
			for note in conn.ReceiveMessage(chat.First(roomname=request.roomname,nickname=request.nickname)):
				yield note


	## method to a  client send a message to chatroom
	def SendMessage(self,request,context):
		global state_file

		print(request.roomname)
		r_id = self.room_identificator(request.roomname)
		print("Send : Id : ",r_id)
		if r_id == self.id:
			aux = self.Validade_User(request.roomname,request.nickname) 
			if aux != None:
				aux.Chats.append({'nickname' : request.nickname,'message' : request.message})
#				aux.Chats.append(request)
				state_file.stack_log('ChatRoom ' + request.roomname + ': Message received from: ' + request.nickname)

			return chat.EmptyResponse()
		else : 
			channel = grpc.insecure_channel(self.address + ':' + str(r_id + 11910))
			conn    = rpc.ChatSServerStub(channel)  ## connection with the server
			print('Connecting to ',r_id + 11910)

			return conn.SendMessage(chat.Note(roomname=request.roomname,nickname=request.nickname,message=request.message))

	def Quit(self,request,context):
		aux = self.Validade_User(request.roomname,request.nickname) 
		if aux != None:
			aux.Nicknames.remove(request.nickname)

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

	def server_snapshot(self):
		global state_file

		while True:
			tm = time.time()
			if tm % 360 == 0:
				aux   = []
				for i in self.ChatRooms:
					aux.append(i.to_dictionary())
				state = {'time': tm,'server': aux}
				print(state)

				state_file.take_snapshot(state)


if __name__ == '__main__':
	chatServer = ChatServer()

	shared_lock = Lock()
	state_file  = State_file(shared_lock)
	Thread(target=state_file.pop_log).start() # This thread will be responsible to write changes in the log file
#	Thread(target=chatServer.server_snapshot).start()

	server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
	rpc.add_ChatSServerServicer_to_server(chatServer,server)
	print('Starting server, Listenning ...')
	server.add_insecure_port('[::]:' + str(chatServer.getPort()))
	server.start()

while True:
	time.sleep(64*64*100)
