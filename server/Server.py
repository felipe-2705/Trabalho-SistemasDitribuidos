#!/usr/bin/python3

from concurrent import futures
import sys
sys.path.append('../')
from proto import ChatRoom_pb2_grpc as rpc
from proto import ChatRoom_pb2  as chat
import grpc
import queue
import time
from threading import Lock


class ChatServer(rpc.ChatSServerServicer):
    def __init__(self):
        self.ChatRooms = []      ## A list of Rooms (port,roomname,password)
        self.Request_port = 11912   ## a port that will receive join and create Request
        self.NextRoom_port = 11913  ## port that the next chatroom created will be listenning
        self.lock = Lock()         ## to lock acess to critical regions
    def Validade_Room(self,Roomname,password):
        lock.acquire()   ### multiple threas may acess this method at same time. though they cant do it currently
        for rooms in self.ChatRooms:
            if rooms.validate_name(Roomname) and rooms.validate_pass(password):
                return rooms
        lock.release()
        return None

    def CreateChat(self,request: chat.CreateChatRequest,context):
        if self.Validade_Room(request.roomname,request.password) == None:
            newroom = ChatRoom(self.NextRoom_port,request.roomname,request.password)
            lock.acquire()
            self.ChatRooms.append(newroom)
            self.NextRoom_port+=1
            lock.release()
            port = newroom.Join(self,request.nickname)
            return chat.JoinResponse(state = 'sucess',Port = port)
        else:
            return None;

    def JoinChat(self,request: chat.JoinChatRequest,context):
        room = self.Validade_Room(request.roomname,request.password)
        if room != None:
            port =room.Join(request.nickname)
            if port != None:
                return chat.JoinResponse(state = 'sucess', Port = port)

        return chat.JoinResponse(state = 'fail',Port = None)
    def getPort(self):
        return self.Request_port
class ChatRoom(rpc.ChatRoomServicer):
    def __init__(self,Port,Roomname,password):
        self.Chats = []            ## Blocking queue to save all chats
        self.Nicknames = []        ## list of participantes Nicknames
        self.Port = Port           ## Port to access this room
        self.Name = Roomname       ## Room name
        self.Password = password   ## Password
        self.lock = Lock()         ## to Block the acess to chats list
        self.locknick = Lock()     ## to Block Nicknames list
        Roomserver = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        rpc.add_ChatRoomServicer_to_server(self,Roomserver)
        print('Starting new Chat room, listenning ...')
        Roomserver.add_insecure_port('[::]:'+ str(self.Port))
    def validate_name(self,Roomname):
        if Roomname == self.Name:
            return True;
        else:
            return False

    def validate_pass(self,password):
        if self.Password == password:
            return True
        else:
            return False

    def get_chats(self):
        return self.Chats

    ## method to a  client send a message to chatroom
    def SendMessage(self,request: chat.Note,context):
        self.lock.acquire()
        self.Chats.append(request)
        self.lock.release()
        return chat.EmptyResponse()

    def ReceiveMessage(self,request_iterator,context):
        lastindex = 0

        # this method will run in each client to receive all messages
        # send all new messages to clients
        while True:
            while lastindex < len(self.Chats):
                self.lock.acquire()
                n = self.Chats[lastindex]
                self.lock.release()
                lastindex+=1
                yield n

    def Quit(self,request: chat.QuitRequest, context):
        self.locknick.acquire()
        self.Nicknames.remove(request.nickname)
        self.locknick.release()

    def Join(self,Nickname):
        ## See if there are any User with the same requested nick
        for nick in self.Nicknames:
            if nick == Nickname:
                return None
        ## Add the user to the Room users List Nicknames
        self.locknick.acquire()
        self.Nicknames.append(Nickname)
        self.locknick.release()
        return self.Port


    def getport(self):
        return self.Port

if __name__ == '__main__':
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chatServer = ChatServer()
    rpc.add_ChatSServerServicer_to_server(chatServer,server)

    print('Starting server, Listenning ...')
    server.add_insecure_port('[::]:'+str(chatServer.getPort()))

   ## the other threads will work this one just need to start others and sleep
    while True:
        time.sleep(64*64*100)
