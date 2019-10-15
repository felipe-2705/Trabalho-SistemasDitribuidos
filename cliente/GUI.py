import tkinter as tk


class RoomLogin:
    roomname = ""
    password = ""
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Room Login")
        self.roomlabel = tk.Label(self.window,text ="Room Name:").grid(row=0,column=0)
        self.passlabel = tk.Label(self.window,text="Password:").grid(row=1,column=0)
        self.roomentry = tk.Entry(self.window)
        self.roomentry.grid(row=0,column=1)
        self.passentry = tk.Entry(self.window)
        self.passentry.grid(row=1,column=1)
        self.ok_btn = tk.Button(self.window,text="OK",command= self.gettext).grid(columnspan=2)
        self.roomname =""
        self.password= ""
    def gettext(self):
        self.roomname =  self.roomentry.get()
        self.password = self.passentry.get()
    def windowStart(self):
        self.window.mainloop()
    def visible(self,bool):
        if bool == True:
            self.window.deiconify()
        else:
            self.window.withdraw()

#room._init_()

class joinlogin:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Join Room")
        self.roomlabel = tk.Label(self.window,text="Room name").grid(row=0,column=0)
        self.passlabel = tk.Label(self.window,text="Password").grid(row=1,column=0)
        self.roomentry = tk.Entry(self.window)
        self.passentry = tk.Entry(self.window)
        self.roomentry.grid(row=0,column=1)
        self.passentry.grid(row=1,column=1)
        self.join_btn = tk.Button(self.window,text="Join",command=self.gettext).grid(columnspan=2)
    def gettext(self):
        self.roomname = self.roomentry.get()
        self.password = self.passentry.get()
    def windowStart(self):
        self.window.mainloop()
    def visible(self,bool):
        if bool == True:
            self.window.deiconify()
        else:
            self.window.withdraw()

class option_menu:
    roomlogin = RoomLogin()
    roomlogin.visible(False)
    wjoin = joinlogin()
    wjoin.visible(False)
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Menu")
        self.create_btn = tk.Button(self.window,text = "Create Room",command = self.create).grid(row=0,columnspan=2)
        self.join_btn = tk.Button(self.window,text="Join Room",command=self.join).grid(row=1,columnspan=2)
    def windowStart(self):
        self.window.mainloop()
    def create(self):
        self.roomlogin.visible(True)
        self.wjoin.visible(False)
    def join(self):
       self.roomlogin.visible(False)
       self.wjoin.visible(True)
       self.chatroom = chatRoom()



class chatRoom:
    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry("500x700")
        self.text = tk.scrolledtext.ScrolledText(self.window)
        self.text.grid(rowspan = 4, columnspan =3)
        self.entrada = tk.Entry(self.window)
        self.entrada.grid(row = 4 , columnspan = 2)
        self.send_btn = tk.Button(self.window,text ="Send",command = self.sendmsg).grid(row=4,column=2)
    def sendmsg(self):
        mensagem = self.entrada.get()
        self.text.insert(mensagem)
    def visible(self,bool):
        if bool == True:
            self.window.deiconify()
        else:
            self.window.withdraw()

op=option_menu()
op.windowStart()
