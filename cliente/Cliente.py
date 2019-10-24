#!/usr/bin/python3

import threading
import grpc
from threading import Lock
import sys
sys.path.append('../')
from proto import ChatRoom_pb2_grpc as rpc
from proto import ChatRoom_pb2  as chat
import time

address= '0.0.0.0'
port = 11912

class Client:
    def __init__(self):
        channel = grpc.insecure_channel(address + ':' +str(port))
        self.conn = rpc.ChatSServerStub(channel)  ## connection with the server
        self.lock = Lock()
        self.chats =[]                    ## lock to chats list

    def Join_to_chatRoom(self,Roomname,Password,Nickname):
        response = self.conn.JoinChat(chat.JoinChatRequest(roomname =Roomname, password = Password, nickname = Nickname))
        if response.state == 'sucess':
            self.Nickname = Nickname
            self.chats.clear()  ## remove any old chat that could be in the chat list
            room_channel = grpc.insecure_channel(address+':'+str(response.Port))
            self.roomconn = rpc.ChatRoomStub(room_channel)
            threading.Thread(target=self.__listen_for_messages,daemon =True).start()
            return True
        else:
            return False

    def Create_chatRoom(self,Roomname,Password,Nickname):
        response = self.conn.CreateChat(chat.CreateChatRequest(roomname = Roomname, password = Password,nickname = Nickname))
        if response.state == 'sucess':
            self.Nickname = Nickname
            self.chats.clear()
            room_channel = grpc.insecure_channel(address+':'+str(response.Port))
            self.roomconn = rpc.ChatRoomStub(room_channel)
            threading.Thread(target=self.__listen_for_messages,daemon=True).start()
            return True
        else:
            return False

    def Send_message(self,Message):
        if Message != '':
            n = chat.Note(nickname = self.Nickname,message = Message)
            self.roomconn.SendMessage(n)


    def __listen_for_messages(self):
        for note in self.roomconn.ReceiveMessage(chat.EmptyResponse()):
            self.chats.append(note)

    def getchat(self,index):
         n =self.chats[index]
         return n
    def getchat_len(self):
         return len(self.chats)
