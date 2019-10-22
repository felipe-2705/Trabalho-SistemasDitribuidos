#!/usr/bin/python3

from concurrent import futures
import sys
sys.path.append('../')
from proto import ChatRoom_pb2_grpc as rpc
from proto import ChatRoom_pb2  as chat
import grpc
import time
from threading import Lock
import os

class ChatRoom(rpc.ChatRoomServicer):
    def __init__(self,Roomname,password):
        self.Chats = []            ## Blocking queue to save all chats
        self.Nicknames = []        ## list of participantes Nicknames
        #self.Port = Port           ## Port to access this room
        self.Name = Roomname       ## Room name
        self.Password = password   ## Password
        self.lock = Lock()         ## to Block the acess to chats list
        self.locknick = Lock()     ## to Block Nicknames list

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
    def SendMessage(self,request,context):
        self.lock.acquire()
        self.Chats.append(request)
        self.lock.release()
        print('ChatRoom: Message received from: '+request.nickname)
        print(request.message)
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

    def Quit(self,request, context):
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

    def setport(self,port):
        self.Port = port

    def getport(self):
        return self.Port


def Room_start(Roomname,password,pipeout):
    print('ChatRroom: Room process started ...')
    Roomserver = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    newroom = ChatRoom(Roomname,password)
    rpc.add_ChatRoomServicer_to_server(newroom,Roomserver)
    print('ChatRoom: Starting new Chat room, listenning ...')
    Port=Roomserver.add_insecure_port('[::]:'+ str(0))
    newroom.setport(Port)
    w=os.fdopen(pipeout,'w')
    w.write(str(Port))
    w.close()
    print('ChatRoom: Pipe Write  ...')
    print('ChatRoom: ' +Roomname+':'+str(Port))
    Roomserver.start();
    while True:
        time.sleep(10*10*64)
