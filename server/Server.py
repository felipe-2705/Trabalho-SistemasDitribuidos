#!/usr/bin/python3

import ChatRoom_pb2_grpc.py as rpc
import ChatRoom_pb2.py as chat
from concurrent import futures
import grpc
import queue
import os

Invalid_Room = {
   'Port': 0,
   'Name': "",
   'Password':""
}


class ChatServer:
    def __init__(self):
        self.ChatRooms = []         ## A list of Rooms (port,roomname,password)
        self.Request_port = 11912   ## a port that will receive join and create Request
        self.NextRoom_port = 11913  ## port that the next chatroom created will be listenning
    def Validade_Room(self,Roomname,password):
        global Invalid_Room
        for rooms in self.ChatRooms:
            if rooms['Name'] == Roomname and rooms['Password'] == password:
                return rooms
        return Invalid_Room
    def CreateChatRoom(self,Roomname,password);
        global Invalid_Room
        if self.Validade_Room(Roomname,password) == Invalid_Room:
            newroom ={
              'Port' = self.NextRoom_port,
              'Name' = Roomname,
              'Password' =  password
            }
            self.ChatRooms.append(newroom)
            self.NextRoom_port+=1
            return newroom
        else:
            return Invalid_Room;
    def JoinChatRoom(self,Roomname,password)
        room = self.Validade_Room(Roomname,password)

class ChatRoom:
    def __init__(self,Port,Roomname,password):
        self.Chats = queue.Queue() ## Blocking queue to save all chats
        self.Nicknames = []        ## list of participantes Nicknames
        self.Port = Port
        self.Name = Roomname
        self.Password = password
                        
