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
import os
from State import *

class ChatRoom(rpc.ChatRoomServicer):
    def __init__(self,Roomname,password,shared_lock):
        self.Port = 0           ## Port to access this room
        self.Chats       = []            ## Blocking queue to save all chats
        self.Nicknames   = []        ## list of participantes Nicknames
        self.Name        = Roomname       ## Room name
        self.Password    = password   ## Password
        self.lock        = Lock()         ## to Block the acess to chats list
        self.locknick    = Lock()     ## to Block Nicknames list

        self.state_file  = State_file(shared_lock) # Will use the received shared lock

    def thread_start(self):
        Thread(target=self.state_file.pop_log).start()          # This thread will be responsible to write changes in the log file

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
        self.Chats.append(request)
        self.state_file.stack_log('ChatRoom: Message received from: ' + request.nickname)
        print('ChatRoom: Message received from: ' + request.nickname)
        return chat.EmptyResponse()

    def ReceiveMessage(self,request_iterator,context):
        lastindex = 0

        # this method will run in each client to receive all messages
        # send all new messages to clients
        while True:
            while lastindex < len(self.Chats):
                n = self.Chats[lastindex]
                lastindex+=1
                yield n

    def Quit(self,request, context):
        self.Nicknames.remove(request.nickname)

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


def Room_start(Roomname,password,pipeout,shared_lock):
    print('ChatRroom: Room process started ...')
    Roomserver = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    newroom    = ChatRoom(Roomname,password,shared_lock)
    newroom.thread_start() #Thread will start

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
