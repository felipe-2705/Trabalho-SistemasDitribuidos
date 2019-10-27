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

class ChatServer(rpc.ChatSServerServicer):
	def __init__(self):
		self.ChatRooms	  = []	  ## List of Rooms will attach a  note
		self.Request_port = 11912   ## Port that will receive join and create Request
		self.lock	  = Lock()  ## Lock acess to critical regions

	# It will write in the log file
	def JoinChat(self,request,context):
		global state_file

		room = self.Validade_Room(request.roomname,request.password)
		if room != None:
			if room.validade_user(request.nickname):
				room.Join(request.nickname)
				print(request.nickname + ' joined ' + request.roomname) # This message
				state_file.stack_log(request.nickname + ' joined ' + request.roomname)

				return chat.JoinResponse(state = 'sucess',Port = None)

		return chat.JoinResponse(state = 'fail',Port = None)

	# It will write in the log_file
	def CreateChat(self,request,context):
		global state_file

		if self.Validade_Room(request.roomname,request.password) == None:
			print('Server: Room validate')
			newroom = room.ChatRoom(request.roomname,request.password,state_file.lock) # Chatroom receive
			newroom.Join(request.nickname)

			self.lock.acquire()
			self.ChatRooms.append(newroom)
			self.lock.release()

			state_file.stack_log('Server: Room ' + request.roomname + ' created ')
			return chat.JoinResponse(state = 'sucess',Port = 0)
		else:
			return chat.JoinResponse(state = 'fail',Port = 0)

	# this method will run in each client to receive all messages
	# send all new messages to clients
	def ReceiveMessage(self,request,context):
		lastindex = 0
		aux = self.Validade_User(request.roomname,request.nickname) 
		if aux != None:
			while True:
				while lastindex < len(aux.Chats):
					n = aux.Chats[lastindex]
					lastindex+=1
					yield n

	## method to a  client send a message to chatroom
	def SendMessage(self,request,context):
		aux = self.Validade_User(request.roomname,request.nickname) 
		if aux != None:
			aux.Chats.append(request)
			self.state_file.stack_log('ChatRoom: Message received from: ' + request.nickname)
			print('ChatRoom: Message received from: ' + request.nickname)

		return chat.EmptyResponse()

	def Quit(self,request,context):
		aux = self.Validade_User(request.roomname,request.nickname) 
		if aux != None:
			aux.Nicknames.remove(request.nickname)

	def Validade_User(self,rommname,user):
		self.lock.acquire()   ### multiple threas may acess this method at same time. though they cant do it currently
		for rooms in self.ChatRooms:
			if rooms.validate_name(roomname) and rooms.validate_user(user):
				return rooms
		self.lock.release()
		return None

	def Validade_Room(self,Roomname,password):
		self.lock.acquire()   ### multiple threas may acess this method at same time. though they cant do it currently
		for rooms in self.ChatRooms:
			if rooms.validate_name(Roomname) and rooms.validate_pass(password):
				return rooms
		self.lock.release()
		return None


	def getPort(self):
		return self.Request_port

	def server_snapshot(self):
		global state_file

		while True:
			tm = time.time()
			if tm % 10 == 0:
				print("Write")
				state = {'time': tm,'server': self.ChatRooms}
				state_file.take_snapshot(state)


if __name__ == '__main__':
	chatServer = ChatServer()

	shared_lock = Lock()
	state_file  = State_file(shared_lock)
	print("Get to work bitch")
	Thread(target=state_file.pop_log).start() # This thread will be responsible to write changes in the log file
#	Thread(target=chatServer.server_snapshot).start()

	server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
	rpc.add_ChatSServerServicer_to_server(chatServer,server)
	print('Starting server, Listenning ...')
	server.add_insecure_port('[::]:' + str(chatServer.getPort()))
	server.start()

while True:
	time.sleep(64*64*100)
