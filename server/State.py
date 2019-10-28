#!/usr/bin/python3

import json
import queue
import time

# Question 1 : How to thread the concurrency of different process trying to acces the same file
#   https://stackoverflow.com/questions/13446445/python-multiprocessing-safely-writing-to-a-file
class State_file:
	# It will create the file if it doens exists
	# Two options :
	#	1 - Server create thread to write_log
	#	  - Each client put a log in the queue
	#	  - The thread will be responsible to get the log written
	#	2 - Each cliente call a methdod to write_log directly
	#	  - lock will be used for concurrent access
	#	3 - Each cliente put a message on the list
	#	  - Each process create a thread to write the file
	#	  - All the process have a shared lock
	def __init__(self,shared_lock):
		self.f_name = "/home/adriano/GitHub/Trabalho-SistemasDitribuidos/server/server_logs.in"
		self.f_snap = "/home/adriano/GitHub/Trabalho-SistemasDitribuidos/server/server_snap.in"
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
				print("1 : " + str(log))
				self.write_log(log)
				self.lock.release()
			else:
				time.sleep(.5)	
			# if :
			#	break

	# Operation is a stirng
	def write_log(self,log):
		fd = open(self.f_name,"a+")
		fd.write(str(log) + "\n")
		fd.close()

	def take_snapshot(self,state):
		self.lock.acquire()

		fd = open(self.f_snap,"a+")
		json.dump(state,fd)
		fd.write("\n")
		fd.close()

		self.lock.release()
