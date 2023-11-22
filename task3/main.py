import asyncio
import websockets
import json

class ChatServer:
    def __init__(self):
        self.clients = set()
        self.rooms = {}
        self.names = {}

    async def handle_client(self, websocket):
        self.clients.add(websocket)

        #await websocket.send(json.dumps({'type': 'ask_name'}))
        user_name_message = await websocket.recv()
        user_name_data = json.loads(user_name_message)
        user_name = user_name_data.get('name')
        self.names[user_name] = websocket

        print(f"Client {websocket} connected.")

        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        finally:
            self.clients.remove(websocket)
            print(f"Client {websocket} disconnected.")

    async def handle_message(self, sender, message):
        data = json.loads(message)
        message_type = data.get('type')

        if message_type == 'join':
            await self.handle_join(sender, data)
        elif message_type == 'message':
            await self.handle_chat_message(sender, data)
        elif message_type == 'private':
            await self.handle_private_message(sender, data)

    async def handle_join(self, sender, data):
        room_name = data.get('room')
        name = data.get('name')
        self.rooms.setdefault(room_name, set()).add(sender)

        join_message = {'type': 'message', 'room': room_name, 'message': f'{name} joined {room_name}!', 'name': name}
        await self.broadcast(room_name, join_message)

        print(f'User {name} has joined the {room_name} room')

    async def handle_chat_message(self, sender, data):
        room_name = data.get('room')
        message = data.get('message')
        name = data.get('name')

        chat_message = {'type': 'message', 'room': room_name, 'message': message, 'name': name}
        await self.broadcast(room_name, chat_message)
    
    async def handle_private_message(self, sender, data):
        recipient = data.get('recipient')
        message = data.get('message')
        name = data.get('name')

        private_message = {'type': 'private', 'name': name, 'message': message}

        if recipient in self.names.keys():
            await self.names[recipient].send(json.dumps(private_message))
            await self.names[name].send(json.dumps(private_message))

    async def broadcast(self, room, message):
        if room in self.rooms:
            for client in self.rooms[room]:
                await client.send(json.dumps(message))

    async def server(self, host, port):
        server = await websockets.serve(self.handle_client, host, port, ping_timeout=60, ping_interval=20)
        print(f"Server started. Listening on {host}:{port}")
        await server.wait_closed()

async def main():
    chat_server = ChatServer()
    try:
        await chat_server.server("localhost", 8765)
    except KeyboardInterrupt:
        print("Server stopped by user.")

if __name__ == "__main__":
    asyncio.run(main())