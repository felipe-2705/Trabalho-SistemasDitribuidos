#!/usr/bin/python3

from concurrent import futures
import sys
sys.path.append('../')
import grpc
import time
from threading import Lock
from threading import Thread
import os
from State import *

class ChatRoom():
	def __init__(self,Roomname,password,shared_lock):
		self.Chats	= []	    ## (Snapshot) Blocking queue to save all chats
		self.Nicknames  = []	    ## (Snapshot) list of participantes Nicknames
		self.Name	= Roomname  ## (Snapshot) Room name
		self.Password	= password  ## (Snapshot) Password
		self.lock	= Lock()    ## to Block the acess to chats list
		self.locknick	= Lock()    ## to Block Nicknames list

		self.state_file = State_file(shared_lock) # Will use the received shared lock

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

	def validade_user(self,nick):
		for nick in self.Nicknames:
			if nick == Nickname:
				return True
		return False

	def new_message(self,mesg):
		self.Chats.append(request)

	def get_chats(self):
		return self.Chats

	def Join(self,Nickname):
		## Add the user to the Room users List Nicknames
		self.locknick.acquire()
		self.Nicknames.append(Nickname)
		self.locknick.release()



	def thread_start(self):
		Thread(target=self.state_file.pop_log).start()		  # This thread will be responsible to write changes in the log file

	def chat_snapshot(self):
		while True:
			tm = time.time()
			if tm % 10 == 0:
				print("Write")
				state = {'time': tm,'name': self.Name,'password': self.Password,'users': self.Nicknames,'mesgs': self.Chats}
				state_file.take_snapshot(state)

