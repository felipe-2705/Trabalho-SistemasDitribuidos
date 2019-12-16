#!/usr/bin/python3

import threading
import grpc
from threading import Lock
import multiprocessing as mp
import sys
sys.path.append('../')
from proto import ChatRoom_pb2_grpc as rpc
from proto import ChatRoom_pb2  as chat
import time

address = '0.0.0.0'
port    = 12000

class Client:
    def __init__(self):
        channel    = grpc.insecure_channel(address + ':' + str(port))
        self.conn  = rpc.ChatSServerStub(channel)  ## connection with the server
        self.lock  = Lock()
        self.chats = []                    ## lock to chats list

    def Join_to_chatRoom(self,Roomname,Password,Nickname):
        response = self.conn.JoinChat(chat.JoinChatRequest(roomname=Roomname, password=Password, nickname=Nickname))
        print(response.state)
        if response.state == 'sucess':
            self.Nickname = Nickname
            self.Roomname = Roomname
            self.chats.clear()  ## remove any old chat that could be in the chat list
            self.start_Listenner()
            return True
        else:
            return False

    def Create_chatRoom(self,Roomname,Password,Nickname):
        response = self.conn.CreateChat(chat.CreateChatRequest(roomname=Roomname, password=Password, nickname=Nickname))
        if response.state == 'sucess':
            print('Sucess')
            self.Nickname = Nickname
            self.Roomname = Roomname
            self.chats.clear()
            self.start_Listenner()
            print('Time to fail')
            return True
        else:
            return False

    def Send_message(self,Message):
        if Message != '':
            n = chat.Note(roomname=self.Roomname, nickname=self.Nickname, message=Message)
            self.conn.SendMessage(n)

    def start_Listenner(self):
        self.listenner = threading.Thread(target=self.__listen_for_messages,daemon=True)
        self.listenner.start()

    def __listen_for_messages(self):
        print("Listen")
        for note in self.conn.ReceiveMessage(chat.First(roomname=self.Roomname, nickname=self.Nickname)):
            self.chats.append(note)

    def getchat(self,index):
         n = self.chats[index]
         return n

    def getchat_len(self):
         return len(self.chats)

    def Quit(self):
        q = chat.QuitRequest(roomname=self.Roomname,nickname = self.Nickname)
        self.conn.Quit(q)
        self.Roomname =''
        self.Nickname =''
