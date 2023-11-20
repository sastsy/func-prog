import asyncio
import websockets
import json
import concurrent.futures
import base64


class ChatServer:
    def __init__(self):
        self.clients = set()
        self.rooms = {}

    async def handle_client(self, websocket):
        self.clients.add(websocket)
        print(self.clients)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        finally:
            self.clients.remove(websocket)

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
        self.rooms.setdefault(room_name, set()).add(sender)
        
        data = {'type': 'message', 'room': room_name, 'message': f'{sender} joined {room_name}!'}

        # await self.handle_chat_message(self, sender, data)
        print(f'User {sender} has joined the {room_name} room')

    async def handle_chat_message(self, sender, data):
        room_name = data.get('room')
        message = data.get('message')

        if room_name in self.rooms:
            recipients = self.rooms[room_name]
            for recipient in recipients:
                if recipient != sender:
                    await recipient.send(json.dumps({'type': 'message', 'room': room_name, 'message': message}))
                    print(f'The message: "{message}" has been sent to participant {recipient} in {room_name} from {sender}')
    
    async def handle_private_message(self, sender, data):
        recipient = data.get('recipient')
        message = data.get('message')

        if recipient in self.clients:
            await recipient.send(json.dumps({'type': 'private', 'message': message, 'sender': sender}))
            print(f'{recipient} got a message: "{message}" from {sender}')

    async def server(self, host, port):
        server = await websockets.serve(self.handle_client, host, port, ping_timeout=60, ping_interval=20)
        print(f"Server started. Listening on {host}:{port}")
        await server.wait_closed()

async def main():
    chat_server = ChatServer()
    await chat_server.server("localhost", 8765)


if __name__ == "__main__":
    asyncio.run(main())