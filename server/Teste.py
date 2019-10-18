#!/usr/bin/python3


import threading
import grpc
import sys
sys.path.append('../')
from proto import ChatRoom_pb2_grpc as rpc
from proto import ChatRoom_pb2 as chat

address = '127.0.0.1'
port = 11912

print('Testing Server Connection ...')

channel = grpc.insecure_channel(address +':'+str(port))
conn = rpc.ChatSServerStub(channel)
print('Creating a new ChatRoom ...')
newroom_response= conn.CreateChat(chat.CreateChatRequest(roomname = 'Teste', password = '123',nickname = 'Tester'))
if(newroom_response.state == 'sucess'):
    newroom_port = newroom_response.Port
    print('Room created sucessfully...')
else:
    print('Fail to create a room, aborting ...')
    exit(1)

print('Trying to connect to chatRoom ...')
room_channel = grpc.insecure_channel(address+':'+str(newroom_port))
room_conn = rpc.ChatRoomStub(room_channel)

print('Trying to Send a message')
for i in range(100):
    room_conn.SendMessage(chat.Note(nickname = 'Tester',message = 'Ola'))

for i in range (100):
    message = room_conn.ReceiveMessage(chat.EmptyResponse())
    print(message)
