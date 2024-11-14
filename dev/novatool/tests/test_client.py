import asyncio
import aiohttp
import json

async def test_query():
    async with aiohttp.ClientSession() as session:
        # Send a test query
        query = {
            "text": "What is quantum computing?",
            "priority": 1
        }

        try:
            # Send POST request to our server
            async with session.post(
                'http://localhost:8000/ask',
                json=query
            ) as response:
                result = await response.json()
                print(f"Response: {json.dumps(result, indent=2)}")

            # Get server status
            async with session.get('http://localhost:8000/status') as response:
                status = await response.json()
                print(f"\nServer Status: {json.dumps(status, indent=2)}")

        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_query())