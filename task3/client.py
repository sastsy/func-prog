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
        self.root.resizable(True, True)

        self.message_area = scrolledtext.ScrolledText(self.root, width=40, height=15)
        self.message_area.grid(row=0, column=0, columnspan=2)

        self.room_entry = Entry(self.root, width=15)
        self.room_entry.grid(row=1, column=0)

        self.join_button = Button(self.root, text="Join Room", command=self.join_room)
        self.join_button.grid(row=1, column=1)

        self.message_entry_room_name = Entry(self.root, width=15)
        self.message_entry_room_name.grid(row=2, column=0)

        self.message_entry_room = Entry(self.root, width=15)
        self.message_entry_room.grid(row=2, column=1)

        self.send_button_room = Button(self.root, text="Send to Room", command=self.send_message_room)
        self.send_button_room.grid(row=2, column=2)

        self.message_entry_user_name = Entry(self.root, width=15)
        self.message_entry_user_name.grid(row=3, column=0)

        self.message_entry_user = Entry(self.root, width=15)
        self.message_entry_user.grid(row=3, column=1)

        self.send_button_user = Button(self.root, text="Send to User", command=self.send_message_user)
        self.send_button_user.grid(row=3, column=2)

    async def connect(self):
        self.chat_client = ChatClient(self.uri, self)
        print('trying to connect')
        await self.chat_client.connect()
        print('successfully connected')

    def send_message_room(self):
        message = self.message_entry_room.get()
        room = self.message_entry_room_name.get()
        self.message_entry_room.delete(0, tk.END)
        self.message_entry_room_name.delete(0, tk.END)

        if message:
            asyncio.create_task(self.chat_client.send_message_room(room, message))

    def send_message_user(self):
        message = self.message_entry_user.get()
        user = self.message_entry_user_name.get()
        self.message_entry_user.delete(0, tk.END)
        self.message_entry_user_name.delete(0, tk.END)

        if message:
            asyncio.create_task(self.chat_client.send_message_user(user, message))

    def join_room(self):
        room_name = self.room_entry.get()
        print(room_name)
        self.room_entry.delete(0, tk.END)

        if room_name:
            asyncio.create_task(self.chat_client.join_room(room_name))
    
    async def run(self):
        while True:
            self.root.update()
            await asyncio.sleep(.1)


class ChatClient:
    def __init__(self, uri, gui):
        self.uri = uri
        self.websocket = None
        self.gui = gui

    async def connect(self):
        self.websocket = await websockets.connect(self.uri)
        asyncio.create_task(self.receive_messages())

    async def receive_messages(self):
        while True:
            message = await self.websocket.recv()
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'message':
                sender = data.get('sender')
                text = data.get('message')
                room = data.get('room')
                self.gui.message_area.insert(tk.END, f'{sender} in {room} : {text}\n')
            elif message_type == 'private':
                sender = data.get('sender')
                text = data.get('message')
                self.gui.message_area.insert(tk.END, f'Private from {sender}: {text}\n')

    async def send_message_room(self, room_name, message):
        message_data = {'type': 'message', 'room': room_name, 'message': message}
        await self.websocket.send(json.dumps(message_data))

    async def send_message_user(self, user_name, message):
        message_data = {'type': 'private', 'recipient': user_name, 'message': message}
        await self.websocket.send(json.dumps(message_data))
    
    async def join_room(self, room):
        join_data = {'type': 'join', 'room': room}
        await self.websocket.send(json.dumps(join_data))


async def main():
    uri = "ws://localhost:8765"
    chat_gui = ChatClientGUI(uri)
    print('trying to connect')
    await chat_gui.connect()
    print('connected')
    await chat_gui.run()
if __name__ == "__main__":
    asyncio.run(main())