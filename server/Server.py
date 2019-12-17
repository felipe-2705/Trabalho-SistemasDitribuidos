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
from pysyncobj import *
from pysyncobj.batteries import ReplDict, ReplLockManager

# Obs  : main cluster id[0] : 11904 11936 11968 12000
# argv : 1 [numero de replicas], 2 [endereco do server 1], 3 [porta do server 1], 4 [endereco do server 2], 5 [porta do server 2], ...
class MainServer(SyncObj):
	def __init__(self):
		self.replica_address = []                 # array to save replicad addresses (ip,port)
		self.ft_ports        = [int(sys.argv[3])] # array passado a finger table

		n = int(sys.argv[1]) - 1                # number of replicas
		i = 4                                   # controls the argv position
		while n > 0:
			self.replica_address.append((sys.argv[i],str(int(sys.argv[i+1]) + 1))) ## (ip,port,id)
			self.ft_ports.append(int(sys.argv[i+1]))
			i = i + 2
			n = n - 1
		end = []                                 ## it will keep the string address
		for adr in self.replica_address:
			end.append(adr[0] + ':' + adr[1])## 'serverIP:serverPort'

		super(MainServer, self).__init__(sys.argv[2] + ':' + str(int(sys.argv[3]) + 1),end) # self address + list of partners addresses #init replicas

		self.address         = sys.argv[2]      # get ip of first server
		self.Request_port    = int(sys.argv[3]) # get port of first server
		self.ChatRooms	     = []	        ## List of Rooms will attach a  note
		self.lock	     = Lock()           ## Lock acess to critical regions

		self.route_table     = FingerTable(self.ft_ports)
		self.id              = self.route_table.id
		self.state_file      = State_file(Lock(),self.route_table.id) 

		#Test Route Table
#		self.route_table.add_node(5,666)
#		self.route_table.add_node(5,616)
#		self.route_table.add_node(25,606)
#		self.route_table.add_node(25,608)
#		while True:
#			time.sleep(10)

		print("Server id : ",self.id,"(",self.Request_port,")")
#		self.log_creation() # problema com log
		self.go_online()


	def log_creation(self):
		try:
			self.recover_state()
		except:
			pass
		Thread(target=self.state_file.pop_log).start() # This thread will be responsible to write changes in the log file
		Thread(target=self.server_snapshot).start()    # This thread will be responsible to write the snapshots

	def go_online(self):
		# Colocar para os nos adicionarem o main server a sua table e requisitarem a adicao deles no main server table
		if self.id != 0:
			main_servers = [11904,11936,11968,12000]
			for serv in main_servers:
				self.route_table.add_node(0,serv)
				channel   = grpc.insecure_channel(self.address + ':' + str(serv))
				conn      = rpc.ChatSServerStub(channel)
				print("send",self.id,self.Request_port)
				conn.AddNewNode(chat.NewNodeReq(n_id=self.id,port=self.Request_port))

		server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
		rpc.add_ChatSServerServicer_to_server(ChatServer(self),server)
		print('Starting server, Listenning ...')
		server.add_insecure_port('[::]:' + str(self.Request_port))
		server.start()
		server.wait_for_termination()

	# Ideia cada servidor manda a mensagem a funcao vai adicionando em uma lista
	def AddNewNode(self,request,context):
		others = self.route_table.add_node(request.n_id,request.port)
		return others

	def FindResponsible(self,request,context):
		resp_node = self.route_table.responsible_node(request.roomname)
		return resp_node

	# Como o pysyncobj não consegue lidar com objetos complexos (locks, estruturas requisicoes, etc...) foram criadas funcoes auxiliares que serão replicadas no lugar
	def CreateChat(self,roomname,password,nickname):
		print("Create chat")
		if self.Validade_Room(roomname,password) == None:
			newroom = room.ChatRoom(roomname,password) # Chatroom receive
			newroom.Join(nickname)
			self.AuxCreateChat(newroom)
			self.state_file.stack_log('Created;' + nickname + ";" + roomname + ";" + password)
			return True
		else:
			return False

	@replicated
	def AuxCreateChat(self,newroom):
		self.ChatRooms.append(newroom)

	def JoinChat(self,request,context):
		room = self.Validade_Room_Index(request.roomname,request.password)
		if room < len(self.ChatRooms):
			if not self.ChatRooms[room].validate_user(request.nickname):
				print('JoinChat;' + request.nickname + ";" + request.roomname )
				self.AuxJoinChat(room,request.nickname)
				self.state_file.stack_log('JoinChat;' + request.nickname + ";" + request.roomname )

				return chat.JoinResponse(state = 'sucess',Port = 0)
		return chat.JoinResponse(state = 'fail',Port = 0)

	@replicated
	def AuxJoinChat(self,room,nickname):
		self.ChatRooms[room].Join(nickname)

	def ReceiveMessage(self,request,context):
		print("Rcv")
		lastindex = 0
		aux = self.Validade_User(request.roomname,request.nickname)
		if aux != None:
			while True:
				while lastindex < len(aux.Chats):
					n = aux.Chats[lastindex]
					n = chat.Note(roomname=request.roomname, nickname=n['nickname'], message=n['message'])
					lastindex+=1
					yield n

	def SendMessage(self,request,context):
		aux = self.Validade_User_Index(request.roomname,request.nickname)
		print(aux)
		if aux < len(self.ChatRooms):
			print('Message;' + request.nickname + ";" + request.roomname + ";" + request.message)
			self.AuxSendMessage(aux,request.nickname,request.roomname,request.message)
			self.state_file.stack_log('Message;' + request.nickname + ";" + request.roomname + ";" + request.message)

		return chat.EmptyResponse()

	@replicated
	def AuxSendMessage(self,room,nickname,roomname,message):
		self.ChatRooms[room].Chats.append({'nickname' : nickname,'message' : message})

	def Quit(self,request,context):
		aux = self.Validade_User(request.roomname,request.nickname)
		if aux != None:
			print('LeftChat;' + request.nickname + ";" + request.roomname )
			self.state_file.stack_log('LeftChat;' + request.nickname + ";" + request.roomname )
			aux.Chats.append({'nickname':request.nickname,'message' : request.nickname+' quited chat room;'})
			aux.Nicknames.remove(request.nickname)

			return chat.EmptyResponse()

	def Validade_User_Index(self,roomname,user):
		i   = 0
		self.lock.acquire()   ### multiple threas may acess this method at same time. though they cant do it currently
		for rooms in self.ChatRooms:
			if rooms.validate_name(roomname) and rooms.validate_user(user):
				break
			i += 1
		self.lock.release()
		return i

	def Validade_User(self,roomname,user):
		aux = None
		self.lock.acquire()   ### multiple threas may acess this method at same time. though they cant do it currently
		for rooms in self.ChatRooms:
			if rooms.validate_name(roomname) and rooms.validate_user(user):
				aux = rooms
		self.lock.release()
		return aux

	def Validade_Room_Index(self,Roomname,password):
		i   = 0
		self.lock.acquire()   ### multiple threas may acess this method at same time. though they cant do it currently
		for rooms in self.ChatRooms:
			if rooms.validate_name(Roomname) and rooms.validate_pass(password):
				break
			i += 1
		self.lock.release()
		return i
		

	def Validade_Room(self,Roomname,password):
		aux = None
		self.lock.acquire()   ### multiple threas may acess this method at same time. though they cant do it currently
		for rooms in self.ChatRooms:
			if rooms.validate_name(Roomname) and rooms.validate_pass(password):
				aux = rooms
		self.lock.release()
		return aux

	def room_identificator(self,roomname):
		result = hashlib.md5(roomname.encode())
		ident  = int(result.hexdigest(),16) % self.route_table.m

		return ident

	def getPort(self):
		return self.Request_port

	def server_snapshot(self):
		time.sleep(5)
		while True:
			print("Snapshot")
			aux   = []
			for i in self.ChatRooms:
				aux.append(i.to_dictionary())
			tm = time.time()
			state = {'time': tm,'server': aux}
			print("(",self.Request_port,")",state)

			self.state_file.take_snapshot(state)
			time.sleep(10)

	def recover_state(self):
		snap = self.state_file.read_snapshot()
		for r in snap['server']:
			newroom = room.ChatRoom(r['room'],r['password'],self.state_file.lock)
			for u in r['users']:
				newroom.Join(u)
			for m in r['mesgs']:
				newroom.Chats.append(m)
		self.ChatRooms.append(newroom)

		logs = self.state_file.read_log()
		for command in logs:
			if   command[0] == 'Created':
				newroom = room.ChatRoom(command[2],command[3],self.state_file.lock)
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

		

class ChatServer(rpc.ChatSServerServicer):
	def __init__(self,server):
		self.server = server

	def Request_port(self):
		return self.server.Request_port

	def List_ports_to_str(self,ports):
		aux = ""
		for p in ports:
			aux += str(p) + ";"
		return aux

	def Str_to_list_ports(self,ports):
		aux = ports.split(";")
		aux.pop()
		return list(map(int,aux))

	# Vai receber uma porta Finger table vai ser responsavel por manter as várias portas
	def AddNewNode(self,request,context):
		others = self.server.AddNewNode(request,context)
		for tupla in others: # each tupla is an id and a list of ports
			for node in tupla[1]: # member 1 is the list of ports
				try:
					channel   = grpc.insecure_channel(self.server.address + ':' + str(node))
					conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
					conn.AddNewNode(chat.NewNodeReq(n_id=request.n_id,port=request.port))
				except:
					print("Fail on AddNewNode at",node)
		return chat.EmptyResponse()

	# Recebe uma string contendo as portas responsaveis (se vier de uma requisicao) ou uma lista se vier de 
	def FindResponsible(self,request,context):
		resp_node = self.server.FindResponsible(request,context)
		room_name = request.roomname # the name of the room
		resp_serv = resp_node[1][1]  # list of severs that will/might know who handle

		if resp_node[0] :
			return chat.FindRResponse(port=self.List_ports_to_str(resp_serv))

		for serv in resp_serv:
			try:
				channel   = grpc.insecure_channel(self.server.address + ':' + str(serv))
				conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
				return conn.FindResponsible(chat.FindRRequest(roomname=room_name))
			except:
				print("Fail FindResponsible at",serv)
		# O que fazer quando nenhum da certo ?

	#------------------------------------------------------------------------------------------------------------------------------
	def CreateChat(self,request,context):
		print("Create chat")
		resp_node = self.server.FindResponsible(request,context) # Fist - try to descover who will handle the request
		room_name = request.roomname                             # the id of the room
		resp_serv = resp_node[1][1]                              # list of severs that will/might know who handle
		print(resp_serv)

		# Talvez problema devido a atribuicoa resp_serv dentro do for
		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			for serv in resp_serv:
				try:
					channel   = grpc.insecure_channel(self.server.address + ':' + str(serv))
					conn      = rpc.ChatSServerStub(channel)  # connection with the responsible server
					result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
					resp_serv = self.Str_to_list_ports(result.port)
					break
				except:
					print("False Fail Create Chat at",serv)

		# If this server is the one supposed to handle -----------------------------------------------------------------------------
		if self.Request_port() in resp_serv:
			print("I handle",request.roomname,request.password,request.nickname)
			result = self.server.CreateChat(request.roomname,request.password,request.nickname)
			print(result)
			if result :
				return chat.JoinResponse(state = 'sucess',Port = 0)
			else:
				return chat.JoinResponse(state = 'fail',Port = 0)

		# Server knows who will handle --------------------------------------------------------------------------------------------
		print("I know who will handle")
		print("is : ",resp_serv)
		for serv in resp_serv:
			try:
				channel = grpc.insecure_channel(self.server.address + ':' + str(serv))
				conn    = rpc.ChatSServerStub(channel)  ## connection with the responsible server
				result  = conn.CreateChat(chat.CreateChatRequest(roomname=request.roomname,password=request.password,nickname=request.nickname))
				break
			except:
				print("False Fail Create Chat at",serv)

		return result

	#------------------------------------------------------------------------------------------------------------------------------
	def JoinChat(self,request,context):
		resp_node = self.server.FindResponsible(request,context)
		room_name = request.roomname
		resp_serv = resp_node[1][1]

		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			for serv in resp_serv:
				try:
					channel   = grpc.insecure_channel(self.server.address + ':' + str(serv))
					conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
					result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
					resp_serv = self.Str_to_list_ports(result.port)
				except:
					print("False Fail Join Chat at",serv)

		if self.Request_port() in resp_serv:
			return self.server.JoinChat(request,context)

		for serv in resp_serv:
			try:
				channel = grpc.insecure_channel(self.server.address + ':' + str(serv))
				conn    = rpc.ChatSServerStub(channel)
				return conn.JoinChat(chat.JoinChatRequest(roomname=request.roomname,password=request.password,nickname=request.nickname))
				break
			except:
				print("True Fail Join Chat at",serv)
		print("What do i do ?")

	#------------------------------------------------------------------------------------------------------------------------------
	def ReceiveMessage(self,request,context):
		print("Send it all")
		resp_node = self.server.FindResponsible(request,context)
		room_name = request.roomname
		resp_serv = resp_node[1][1]

		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			for serv in resp_serv:
				try:
					channel   = grpc.insecure_channel(self.server.address + ':' + str(serv))
					conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
					result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
					resp_serv = self.Str_to_list_ports(result.port)
				except:
					print("False Fai Receive Message at",serv)

		if self.Request_port() in resp_serv:
			lastindex = 0
			aux = None
			while not aux:
				aux = self.server.Validade_User(request.roomname,request.nickname)
			if aux != None:
				while True:
					while lastindex < len(aux.Chats):
						n = aux.Chats[lastindex]
						n = chat.Note(roomname=request.roomname, nickname=n['nickname'], message=n['message'])
						lastindex+=1
						yield n
		print("What")
		for serv in resp_serv:
			try:
				channel = grpc.insecure_channel(self.server.address + ':' + str(serv))
				conn    = rpc.ChatSServerStub(channel)  ## connection with the server
				for note in conn.ReceiveMessage(chat.First(roomname=request.roomname,nickname=request.nickname)):
					yield note
				break
			except:
				print("Error Receive Message at",serv)

	#------------------------------------------------------------------------------------------------------------------------------
	def SendMessage(self,request,context):
		resp_node = self.server.FindResponsible(request,context)
		room_name = request.roomname
		resp_serv = resp_node[1][1]

		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			for serv in resp_serv:
				try:
					channel   = grpc.insecure_channel(self.server.address + ':' + str(resp_serv))
					conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
					result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
					resp_serv = self.Str_to_list_ports(result.port)
					break
				except:
					print("False Error Send Message at",serv)

		if self.Request_port() in resp_serv:
			print("I handle")
			return self.server.SendMessage(request,context)

		for serv in resp_serv:
			try:
				channel = grpc.insecure_channel(self.server.address + ':' + str(serv))
				conn    = rpc.ChatSServerStub(channel)  ## connection with the server
				return conn.SendMessage(chat.Note(roomname=request.roomname,nickname=request.nickname,message=request.message))
			except:
				print("True Error Send Message at",serv)


	#------------------------------------------------------------------------------------------------------------------------------
	def Quit(self,request,context):
		resp_node = self.server.FindResponsible(request,context)
		room_name = request.roomname
		resp_serv = resp_node[1][1]

		if not resp_node[0]: # Communicate with the server that might know who will respond the request
			for serv in resp_serv:
				try:
					channel   = grpc.insecure_channel(self.server.address + ':' + str(resp_serv))
					conn      = rpc.ChatSServerStub(channel)  ## connection with the responsible server
					result    = conn.FindResponsible(chat.FindRRequest(roomname=room_name))
					resp_serv = self.Str_to_list_ports(result.port)
					break
				except:
					print("False Error Quit at",serv)

		if self.Request_port() in resp_serv:
			return self.server.Quit(request,context)

		for serv in resp_serv:
			try:
				channel = grpc.insecure_channel(self.server.address + ':' + str(serv))
				conn    = rpc.ChatSServerStub(channel)  ## connection with the server
				return conn.Quit(chat.QuitRequest(roomname=request.roomname,nickname=request.nickname))
			except:
				print("True Error Quit at",serv)

if __name__ == '__main__':
	server = MainServer()
	print("Went")
	while True:
		time.sleep(0.25)
