#!/usr/bin/python3

import socket
import threading

host = gethostname()
my_ip = gethostbyname(host)
lport = 16161



def Receive_connection():
    s = socket.socket()
    s.bing(('',port))
    s.listen(5)


    cs,addr = s.accept()
    nome = cs.recv(1024)
    password = cs.recv(1024)

    print('connection received:'+addr)
    print(nome)
    print(password)

    cs.close()
