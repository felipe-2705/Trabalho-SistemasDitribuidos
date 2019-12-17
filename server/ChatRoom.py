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
	def __init__(self,Roomname,password):
		self.Chats	= []	    ## (Snapshot) Blocking queue to save all chats
		self.Nicknames  = []	    ## (Snapshot) list of participantes Nicknames
		self.Name	= Roomname  ## (Snapshot) Room name
		self.Password	= password  ## (Snapshot) Password

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

	def validate_user(self,nick):
		if nick in self.Nicknames:
			return True
		return False

	def new_message(self,mesg):
		self.Chats.append(request)

	def get_chats(self):
		return self.Chats

	def Join(self,Nickname):
		## Add the user to the Room users List Nicknames
		self.Nicknames.append(Nickname)

	# Probably Chats is the problem
	def to_dictionary(self):
		return {'room' : self.Name, 'password' : self.Password,'users' : self.Nicknames,'mesgs' : self.Chats}
