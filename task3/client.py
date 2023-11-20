import asyncio
import websockets
import json
import tkinter as tk
from tkinter import scrolledtext, Entry, Button
from concurrent.futures import ThreadPoolExecutor


# class Client:
#     def __init__(self) -> None:
        


#     async def send_message():
#         uri = "ws://localhost:8765"
#         async with websockets.connect(uri) as websocket:
#             join_data = {'type': 'join', 'room': 'general'}
#             await websocket.send(json.dumps(join_data))

#             message_data = {'type': 'message', 'room': 'general', 'message': 'Hello, World!'}
#             await websocket.send(json.dumps(message_data))

#             #private_message = {'type': 'private', 'recipient': }

# asyncio.get_event_loop().run_until_complete(send_message())
class ChatClientGUI:
    def __init__(self, uri):
        self.uri = uri
        self.chat_client = None
        self.root = tk.Tk()
        self.root.title("Chat Client")
    
        self.message_area = scrolledtext.ScrolledText(self.root, width=40, height=15)
        self.message_area.grid(row=0, column=0, columnspan=3)

        self.room_entry = Entry(self.root, width=15)
        self.room_entry.grid(row=1, column=0)
        self.join_button = Button(self.root, text="Join Room", command=lambda: self.create_task(self.join_room))
        self.join_button.grid(row=1, column=2)

        self.message_entry_room_name = Entry(self.root, width=15)
        self.message_entry_room_name.grid(row=2, column=0)
        self.message_entry_room = Entry(self.root, width=15)
        self.message_entry_room.grid(row=2, column=1)
        self.send_button_room = Button(self.root, text="Send to Room", command=lambda: self.create_task(self.send_message_room))
        self.send_button_room.grid(row=2, column=2)

        self.message_entry_user_name = Entry(self.root, width=15)
        self.message_entry_user_name.grid(row=3, column=0)
        self.message_entry_user = Entry(self.root, width=15)
        self.message_entry_user.grid(row=3, column=1)
        self.send_button_user = Button(self.root, text="Send to User", command=lambda: self.create_task(self.send_message_user))
        self.send_button_user.grid(row=3, column=2)

    async def connect(self):
        self.chat_client = ChatClient(self.uri, self)
        print('trying to connect')
        await self.chat_client.connect()
        print('successfull connection')

    async def send_message_room(self):
        message = self.message_entry_room.get()
        room = self.message_entry_room_name.get()
        self.message_entry_room.delete(0, tk.END)
        self.message_entry_room_name.delete(0, tk.END)

        if message:
            await self.chat_client.send_message_room(room, message)
    
    async def send_message_user(self):
        message = self.message_entry_user.get()
        user = self.message_entry_user_name.get()
        self.message_entry_user.delete(0, tk.END)
        self.message_entry_user.delete(0, tk.END)


        if message:
            await self.chat_client.send_message_user(user, message)

    async def join_room(self):
        room_name = self.room_entry.get()
        print(room_name)
        self.room_entry.delete(0, tk.END)

        if room_name:
            await self.chat_client.join_room(room_name)
    
    def run(self):
        self.root.mainloop()
    
    def create_task(self, coroutine):
        self.chat_client.loop.create_task(coroutine())


class ChatClient:
    def __init__(self, uri, gui):
        self.uri = uri
        self.websocket = None
        self.gui = gui
        self.loop = asyncio.get_event_loop()

    async def connect(self):
        self.websocket = await websockets.connect(self.uri)
        asyncio.create_task(self.receive_messages())

    async def receive_messages(self):
        while True:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                message_type = data.get('type')

                if message_type == 'message':
                    sender = data.get('sender', 'Server')
                    text = data.get('message')
                    self.gui.message_area.insert(tk.END, f'{sender}: {text}\n')
                    print('sent message')
                elif message_type == 'private':
                    sender = data.get('sender', 'Server')
                    text = data.get('message')
                    print('sent private')
                    self.gui.message_area.insert(tk.END, f'Private from {sender}: {text}\n')

            except websockets.exceptions.ConnectionClosedError:
                print("Connection closed unexpectedly.")
                break

            except Exception as e:
                print(f"Error while receiving messages: {e}")
                break

            finally:
                await asyncio.sleep(10)
        
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
    chat_client = ChatClient(uri, chat_gui)
    await chat_client.connect()
    chat_gui.chat_client = chat_client
    print('connected')
    chat_gui.run()
    print('task created')


if __name__ == "__main__":
    asyncio.run(main())