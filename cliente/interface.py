import Cliente
import threading
from threading import Lock
import Cliente
import os

cliente = Cliente.Client()



nome=''
password=''
Nickname= ''
chats = []
Quit = False
lock_chat = Lock()

def getinfo():
    global nome
    global password
    global Nickname

    nome = input('Room Name: ')
    password = input('Password: ')
    Nickname = input('Your Nickname:')

def ReceiveMessage():
    global cliente
    global chats
    lastindex = 0
    while True:
        while lastindex < cliente.getchat_len():
            n = cliente.getchat(lastindex)
            lastindex+=1
            mensagem= '['+ n.nickname+'] '+n.message+'\n'
            lock_chat.acquire()
            chats.append(mensagem)
            lock_chat.release()
            reprint()

def reprint():
    os.system('clear')
    lock_chat.acquire()
    for msg in chats:
        print(msg)
    lock_chat.release()

def Room():
    while True:
        msg = input('['+Nickname+'] ' )
        if msg == '!quit':
            break;

        cliente.Send_message(msg)
        #lock_chat.acquire()
        #chats.append('[' +Nickname +'] '+msg)
        #lock_chat.release()
        reprint()

while not Quit:

    menu = '[1] Create Room\n[2] Join Room\n[3] Quit\n'
    op = input(menu)
    os.system('clear')

    if op == '1':
        getinfo()
        if not cliente.Create_chatRoom(nome,password,Nickname):
            print('ERRO','Room was not Possible to Create')
        else:
            threading.Thread(target=ReceiveMessage,daemon=True).start()
            Room()
    elif op == '2':
        getinfo()
        if not cliente.Join_to_chatRoom(nome,password, Nickname):
            print('ERRO','Room was not Possible to Join')
        else:
            threading.Thread(target=ReceiveMessage,daemon=True).start()
            Room()
    elif op == '3':
        Quit =True
    else:
        os.system('clear')
        print('Opçao invalida digite novamente...')

    os.system('clear')
