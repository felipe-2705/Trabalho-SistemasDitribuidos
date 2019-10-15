#!/usr/bin/python3


import socket
import threading

host = socket.gethostname()
my_ip= socket.gethostbyname(host)
port = 16161
s_ip = '192.168.100.9'
Room = ""
password=""
Invalid = 00000
Mensagens=[] # Lista de todas as mensagens na Sala ate o momento; è necessario para a reimpressao de todas as mensagens

def RoomPass()
    Room = input('Room name:')
    password = input('password')

def connect_to_server():
    global port
    s= socket.socket()
    s.connect((s_ip,port)) # conecta ao servidor
    # tenta conectar a alguma sala no servidor
    s.send(Room)
    s.send(password)
    rsp = s.recv(1024) # a rsp sera a porta da room ou pode ser Invalid  indicando que o nome ou a senha estao incorretos
    s.close()
    return rsp



# Enquanto nao connectar a uma sala valida continua
while True:
    os.system('clear')
    RoomPass()
    connect = connect_to_server()
    if connect == Invalid:
        continue
    else:
        port = connect
        break
