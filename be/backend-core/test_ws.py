import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8000/ws/swarm-debate/test-session-1"
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket. Waiting for messages...")
        count = 0
        try:
            while count < 5:  # Just wait for a few messages
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Received: {data.get('agent_name')} - {data.get('status')}")
                count += 1
        except Exception as e:
            print(f"Error: {e}")
            
if __name__ == "__main__":
    asyncio.run(test_ws())
