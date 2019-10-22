#!/usr/bin/python3


import threading
import grpc
import sys
sys.path.append('../')
from proto import ChatRoom_pb2_grpc as rpc
from proto import ChatRoom_pb2 as chat
import time

address = '0.0.0.0'
newroom_port = 11912

#print('Testing Server Connection ...')

#channel = grpc.insecure_channel(address+':'+str(port))
#conn = rpc.ChatSServerStub(channel)
#print('Creating a new ChatRoom ...')
#newroom_response= conn.CreateChat(chat.CreateChatRequest(roomname = 'Teste', password = '123',nickname = 'Tester'))
#if(newroom_response.state == 'sucess'):
#    newroom_port = newroom_response.Port
#    print('Room created sucessfully...')
#else:
#    print('Fail to create a room, aborting ...')
#    exit(1)


print('Trying to connect to chatRoom ...')
room_channel = grpc.insecure_channel(address+':'+str(newroom_port))
room_conn = rpc.ChatRoomStub(room_channel)
time.sleep(10)

def Cliente1():
    print('Cliente1: Trying to Send a message')
    for i in range(100):
        room_conn.SendMessage(chat.Note(nickname = 'Tester',message = str(i)))
        print('Cliente1: Message: '+str(i)+' sent ...')
        

    while True:
        for message in room_conn.ReceiveMessage(chat.EmptyResponse()):
            print(message)

def Cliente2():
    print('Cliente2: Trying to Send a message')
    for i in range(100):
        room_conn.SendMessage(chat.Note(nickname = 'Tester2',message = str(i)))
        print('Cliente2: Message:'+str(i)+'sent ...')


    while True:
        for message in room_conn.ReceiveMessage(chat.EmptyResponse()):
            print(message)


c1=threading.Thread(target=Cliente1,daemon =True)
c2=threading.Thread(target=Cliente2,daemon =True)
c1.start()
c2.start()
c1.join()
c2.join()
