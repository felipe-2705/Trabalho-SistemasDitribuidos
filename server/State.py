#!/usr/bin/python3

import json
import queue
import time

# Question 1 : How to thread the concurrency of different process trying to acces the same file
#   https://stackoverflow.com/questions/13446445/python-multiprocessing-safely-writing-to-a-file
class State_file:
	# It will create the file if it doens exists
	#1 - Server create thread to write_log
	#  - Each client put a log in the queue
	#  - The thread will be responsible to get the log written
	def __init__(self,shared_lock,s_id):
		self.f_name = "/home/adriano/Documentos/Trabalho-SistemasDitribuidos/server/server_logs_" + str(s_id) + ".in"
		self.f_snap = "/home/adriano/Documentos/Trabalho-SistemasDitribuidos/server/server_snap_" + str(s_id) + ".in"
		self.lock   = shared_lock
		self.queue  = []

	# If there is a need for timestamp this is where it should be used
	def stack_log(self,message):
		self.queue.append(message)

	def pop_log(self):
		while True:
			if(len(self.queue) > 0):
				self.lock.acquire()

				log = self.queue.pop(0)
				self.write_log(log)

				self.lock.release()
			else:
				time.sleep(.5)	

	# Operation is a stirng
	def write_log(self,log):
		print(str(log))
		fd = open(self.f_name,"a+")
		fd.write(str(log) + "\n")
		fd.close()

	def take_snapshot(self,state):

		self.lock.acquire()

		fd = open(self.f_snap,"w+")
		json.dump(state,fd)
		fd.write("\n")
		fd.close()
		open(self.f_name, 'w').close()

		self.lock.release()

	def read_log(self):
		fd  = open(self.f_name,"r")
		log = fd.readlines()
		for i in range(len(log)):
			log[i] = log[i].strip("\n").split(";")

		return log

	def read_snapshot(self):
		fd = open(self.f_snap,"r")
		snap = fd.readlines()
		snap = snap[0].strip("\n")
		snap = json.loads(snap) 

		return snap
