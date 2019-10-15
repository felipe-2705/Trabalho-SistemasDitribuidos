import tkinter as tk
from tkinter import scrolledtext



class option_menu:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Menu")
        self.roomlabel = tk.Label(self.window,text="Room name").grid(row=0,column=0)
        self.passlabel = tk.Label(self.window,text="Password").grid(row=1,column=0)
        self.roomentry = tk.Entry(self.window)
        self.passentry = tk.Entry(self.window)
        self.roomentry.grid(row=0,column=1,columnspan=2)
        self.passentry.grid(row=1,column=1,columnspan=2)
        self.create_btn = tk.Button(self.window,text = "Create",command = self.create).grid(row=2,column=0,columnspan=1)
        self.join_btn = tk.Button(self.window,text="Join",command=self.join).grid(row=2,column=1,columnspan=1)
    def windowStart(self):
        self.window.mainloop()
    def create(self):
        print("create")
        ct = chatRoom()
    def join(self):
       print("Join")
       ct = chatRoom()
    def visible(self,bool):
        if bool == True:
            self.window.deiconify()
        else:
            self.window.withdraw()

class chatRoom:
    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry("500x700")
        self.window.title('Chat box')
        self.text = scrolledtext.ScrolledText(self.window,width =60,height=39)
        self.text.grid(row=0,columnspan=5)
        self.entrada = tk.Entry(self.window)
        self.entrada.grid(row=1,column=0,columnspan=3)
        self.send_btn = tk.Button(self.window,text ="Send",command = self.sendmsg).grid(row=1,column=3,columnspan=2)
    def sendmsg(self):
        mensagem = self.entrada.get()
        if mensagem != "":
            self.text.insert(tk.INSERT,mensagem + '\n')
    def visible(self,bool):
        if bool == True:
            self.window.deiconify()
        else:
            self.window.withdraw()
    def insertMsg(self,Msg):
        if Msg != "":
            self.text.insert(tk.Insert,Msg+'\n')

op=option_menu()
op.windowStart()
