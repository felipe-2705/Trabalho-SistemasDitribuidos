#!/usr/bin/python3

from concurrent import futures
import sys
sys.path.append('../')
from proto import ChatRoom_pb2_grpc as rpc
from proto import ChatRoom_pb2  as chat
import grpc
import time
from threading import Lock
from server import ChatRoom as room
import multiprocessing as mp
import os

Roomname = 'Batman'
password = 123
port = 11912

if __name__ == '__main__':
    print('ChatRroom: Room process started ...')
    Roomserver = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    newroom = room.ChatRoom(Roomname,password)
    rpc.add_ChatRoomServicer_to_server(newroom,Roomserver)
    print('ChatRoom: Starting new Chat room, listenning ...')
    Port=Roomserver.add_insecure_port('[::]:'+ str(port))
    newroom.setport(port)
    print('ChatRoom: ' +Roomname+':'+str(Port))
    Roomserver.start();


while True:
    time.sleep(64*64*100)
