import asyncio
import websockets
import json
import tkinter as tk
from tkinter import scrolledtext, Entry, Button


class ChatClientGUI:
    def __init__(self, uri):
        self.uri = uri
        self.chat_client = None
        self.root = tk.Tk()
        self.root.title("Chat Client")
    
        self.message_area = scrolledtext.ScrolledText(self.root, width=40, height=15)
        self.message_area.grid(row=0, column=0, columnspan=2)

        self.message_entry = Entry(self.root, width=30)
        self.message_entry.grid(row=1, column=0)

        self.send_button = Button(self.root, text="Send", command=self.send_message)
        self.send_button.grid(row=1, column=1)

    async def connect(self):
        self.chat_client = ChatClient(self.uri, self)
        await self.chat_client.connect()
    
    def run(self):
        self.root.mainloop()

    def send_message(self):
        message = self.message_entry.get()
        self.message_entry.delete(0, tk.END)

        if message:
            asyncio.create_task(self.chat_client.send_message('general', message))
    
    