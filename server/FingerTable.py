#!/usr/bin/python3

import math
import hashlib

class FingerTable:
	# Passar o ip das replicas
	def __init__(self,ports):
		port = ports[0] # first port will always be this server port

		self.m            = 32                        # max number of servers
		self.n            = round(math.log(self.m,2)) # number of entries in the routing table
		self.id           = port % 32                 # this server id
		self.port         = port
		self.servers      = []                        # routing table
		self.know_servers = ports

		for i in range(self.n):
			self.servers.append((self.id,ports))

	# It keeps control of the entries in the routing table (self.servers)
	# entrada : id e uma porta
	def add_node(self,new_id,port):
#		print("Finger Table")
#		for ix in self.servers:
#			print(ix)
#		print("--------------------")

#		print(new_id,"x",self.id,":",port)
		if (port in self.know_servers) or (new_id == self.id):
#			print("Exit")
			return []

		dist      = self.distance(self.id,new_id)
		selecteds = []

		for i in range(self.n):
			aux = 2 ** i
			if self.servers[i][0] == new_id: # id ja estiver na tabela (agora tem a possibilidade de dar append no membro 2 [lista de portas])
				for tupla in self.servers:
					if tupla[0] == new_id:
						tupla[1].append(port)
						self.know_servers.append(port)
				return selecteds

			if (self.servers[i][0] != self.id) and (self.servers[i] not in selecteds): # Only nodes 'behind' the new node will have the chance to change tables
				selecteds.append(self.servers[i])

			if   dist < aux:
				if i > 0:
					i = i - 1
					break
			elif dist == aux:
				break

		for j in range(i + 1):
			if self.servers[j][0] == self.id:
				self.servers[j] = (new_id,[port])
			if dist < self.distance(self.id,self.servers[j][0]):
				self.servers[j] = (new_id,[port])

		return selecteds
		## Tupla com id e lista de portas

	def responsible_node(self,roomname):
		ident = self.room_identificator(roomname)
		dist  = self.distance(self.id,ident)

		# Garantee to know
		# This order needs to be kept
		# First check the dist to entry 0 and the the dist to entry 1
		if   dist == 0:
			return (True,(self.id,self.port))
		elif dist == 1:
			return (True,self.servers[0])
		elif dist == 2:
			return (True,self.servers[1])

		# The i - 1 e i + 1 is to differentiate if a node breaked or finished the loop
		for i in range(2,self.n):
			if ident == self.servers[i][0]:
				return (True,self.servers[i])
			if dist <= (2 ** i):
				i = i - 1
				break
		i = i + 1
		if i == self.n:
			if self.servers[i - 1][0] == self.id:
				return (True,self.servers[i - 1])
			return (False,self.servers[i - 1])
		if self.servers[i][0] != self.servers[i - 1][0]:
			return(False,self.servers[i - 1])
		# self.servers[i][0] == self.servers[i - 1][0]
		return (True,self.servers[i])

	# Maybe subtract 1 to count the nodes in between
	def distance(self,a,b):
		if a > b:
			return (b + self.m - a)
		return (b - a)

	# Will return the id of the server that will store this data
	def room_identificator(self,roomname):
		result = hashlib.md5(roomname.encode())
		ident  = int(result.hexdigest(),16) % self.m

		return ident

#if __name__ == '__main__':
#	Room ids test
#	ft = FingerTable([1])
#	r_names = ["room","r00m","ro0m","r0om"]
#	ro0m
#	r0om
#	for r in r_names:
#		print(r,"->",ft.room_identificator(r))
#
#
# Add node test
#	print(ft.add_node(7,11913))
#	print(ft.add_node(12,11941))
#	print(ft.add_node(15,11941))
#	print(ft.add_node(14,11941))
#	print(ft.add_node(18,11941))
#	print(ft.add_node(20,11941))
#	print(ft.add_node(21,11941))
#	print(ft.add_node(28,11941))
#
# Routing test
#	print(ft.servers)
#	for x in range(32):
#		print(x)
#	rn = ft.responsible_node(1)
#	print(rn)
#		print("-------------------------")
