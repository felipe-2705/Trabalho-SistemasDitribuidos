#!/usr/bin/python3

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
		self.f_name = "/home/adriano/GitHub/SD/Trabalho-SistemasDitribuidos/server/server_state.in"
		self.lock   = shared_lock
#		self.queue  = queue.Queue()
		self.queue  = []
#		fd = open(self.f_name,"r+") # We have to thrust the file exists
#		fd.close()
	
	def stack_log(self,message):
		print("Append")
		self.queue.append(message)

	def pop_log(self):
		print("Ready to work")
		while True:
			if(len(self.queue) > 0):
				self.lock.acquire()

				log = self.queue.pop(0)
				self.write_log(log)

				self.lock.release()
			else:
				time.sleep(.5)	
			# if :
			#	break

#	# Maybe this function will be changed to put a timer in the message
#	def stack_log(self,message):
#		self.queue.put(message)
#
#	def write_log_queue(self):
#		while True:
#			new_log = self.queue.get(timeout=.5)
#			self.write_log(new_log)
#			self.queue.task_done()
#			#if :
#			#	break

	# Operation is a stirng
	# It will be changed if theres a need to struct the data
	def write_log(self,operation):
		fd = open(self.f_name,"a")
		fd.write(str(operation) + "\n")
		fd.close()

#	def data_snapshot(self,operation):

#	def read_file(self):
