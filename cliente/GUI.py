import tkinter as tk
from tkinter import scrolledtext
import Cliente

cliente = Cliente.Client()
class option_menu:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Menu")
        #self.window.geometry("100x250")
        self.roomlabel = tk.Label(self.window,text="Room name").grid(row=0,column=0)
        self.passlabel = tk.Label(self.window,text="Password").grid(row=1,column=0)
        self.roomentry = tk.Entry(self.window)
        self.passentry = tk.Entry(self.window)
        self.roomentry.grid(row=0,column=1,columnspan=3)
        self.passentry.grid(row=1,column=1,columnspan=3)
        self.nick =tk.Label(self.window,text = "Nickname").grid(row =2, column=0)
        self.nickentry = tk.Entry(self.window)
        self.nickentry.grid(row=2,column=1,columnspan=3)
        self.create_btn = tk.Button(self.window,text = "Create",command = self.create).grid(row=3,column=0,columnspan=1)
        self.join_btn = tk.Button(self.window,text="Join",command=self.join).grid(row=3,column=1,columnspan=1)

    def windowStart(self):
        self.window.mainloop()
    def create(self):
        global cliente
        self.roomname = self.roomentry.get()
        self.password = self.passentry.get()
        self.nickname = self.nickentry.get()
        if not cliente.Create_chatRoom(self.roomname,self.password,self.nickname):
            tk.messagebox.showerror('ERRO','Room was not Possible to Create')
        else:
            ct = chatRoom(self.nickname,self.roomname)
    def join(self):
        global cliente
        self.roomname = self.roomentry.get()
        self.password = self.passentry.get()
        self.nickmane = self.nickentry.get()
        if not cliente.Join_to_chatRoom(self.roomname,self.password, self.nickname):
            tk.messagebox.showerror('ERRO','Room was not Possible to Join')
        else:
            ct = chatRoom(self.nickname,self.roomname)
    def visible(self,bool):
        if bool == True:
            self.window.deiconify()
        else:
            self.window.withdraw()

class chatRoom:
    def __init__(self,nick,Roomname):
        self.nickname = nick
        self.window = tk.Tk()
        self.window.geometry("500x700")
        self.window.title(Roomname)
        self.text = scrolledtext.ScrolledText(self.window,width =60,height=39)
        self.text.configure(state = "disabled")
        self.text.grid(row=0,columnspan=5)
        self.entrada = tk.Entry(self.window)
        self.entrada.grid(row=1,column=0,columnspan=3)
        self.send_btn = tk.Button(self.window,text ="Send",command = self.sendmsg).grid(row=1,column=3,columnspan=2)
        threading.Thread(target=self.ReceiveMenssagem,daemon=True).start()  ## thread to print incoming menssages
    def sendmsg(self):
        global cliente
        mensagem = self.entrada.get()
        if mensagem != "":
            self.cliente.Send_message(mensagem)
            self.text.configure(state = "normal")
            self.text.insert(tk.INSERT,'['+self.nickname +']'+ ' '+mensagem + '\n')
            self.text.configure(state = "disabled")

    def ReceiveMenssagem(self):
        global cliente
        lastindex = 0
        while True:
            while lastindex < cliente.getchat_len():
                n = cliente.getchat(lastindex)
                self.insertMsg('['+ n.nickname+'] '+n.message+'\n')

    def visible(self,bool):
        if bool == True:
            self.window.deiconify()
        else:
            self.window.withdraw()
    def insertMsg(self,Msg):
        if Msg != "":
            self.text.configure(state = "normal")
            self.text.insert(tk.Insert,Msg+'\n')
            self.text.configure(state = "disabled")

if __name__ == '__main__':
    print('Starting Client...')
    op=option_menu()
    op.windowStart()
