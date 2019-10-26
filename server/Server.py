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
        self.ChatRooms    = []      ## List of Rooms will attach a  note
        self.Request_port = 11912   ## Port that will receive join and create Request
        self.lock         = Lock()  ## Lock acess to critical regions

    def Validade_Room(self,Roomname,password):
        self.lock.acquire()   ### multiple threas may acess this method at same time. though they cant do it currently
        for rooms in self.ChatRooms:
            if rooms.validate_name(Roomname) and rooms.validate_pass(password):
                return rooms
        self.lock.release()
        return None

    # It will write in the log_file
    def CreateChat(self,request,context):
        global state_file

        if self.Validade_Room(request.roomname,request.password) == None:
            print('Server: Room validate')
#            newroom = room.ChatRoom(request.roomname,request.password)
            newroom = room.ChatRoom(request.roomname,request.password,state_file.lock) # Chatroom receive

            self.lock.acquire()
            self.ChatRooms.append(newroom)
            self.lock.release()

            r,w = os.pipe()
            print('Server: pipe created ...')
            p = mp.Process(target= room.Room_start,args=(request.roomname,request.password,w,state_file.lock)) # Room_start is the new process
            print('Server: Room process created') ## Probably this message
            Thread(target=run_room,args=(p,),daemon=True).start() #Thread to rn the process
            r = os.fdopen(r)
            print('Server: Pipe Read')
            port_s = r.read()
            port = int(port_s)
            print('Port:' + str(port))
            r.close()

            state_file.stack_log('Server: Room ' + request.roomname + ' created at ' + str(port))
            newroom.setport(port)
            return chat.JoinResponse(state = 'sucess',Port = port)
        else:
            return chat.JoinResponse(state = 'fail',Port = port);

    # It will write in the log file
    def JoinChat(self,request,context):
        global state_file

        room = self.Validade_Room(request.roomname,request.password)
        if room != None:
            port =room.Join(request.nickname)
            if port != None:
                print(request.nickname +' joined ' + request.roomname) # This message
                state_file.stack_log(request.nickname +' joined ' + request.roomname)
                return chat.JoinResponse(state = 'sucess', Port = port)

        return chat.JoinResponse(state = 'fail',Port = None)

    def getPort(self):
        return self.Request_port

def run_room(p):
    p.run()

if __name__ == '__main__':
    shared_lock = Lock()
    state_file  = State_file(shared_lock)
    print("Get to work bitch")
    Thread(target=state_file.pop_log).start() # This thread will be responsible to write changes in the log file

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    chatServer = ChatServer()
    rpc.add_ChatSServerServicer_to_server(chatServer,server)
    print('Starting server, Listenning ...')
    server.add_insecure_port('[::]:'+str(chatServer.getPort()))
    server.start()

    mp.set_start_method('spawn') ## set processes start methods to new process independent
   ## the other threads will work this one just need to start others and sleep
while True:
    time.sleep(64*64*100)
