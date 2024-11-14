import asyncio
import aiohttp
import random
from rich.console import Console

async def simulate_client(session, client_id: int, num_queries: int):
    console = Console()
    base_url = "http://localhost:8000"

    test_queries = [
        "What is quantum computing?",
        "How do neural networks work?",
        "Explain blockchain technology",
        "What is machine learning?",
        "How does natural language processing work?"
    ]

    for i in range(num_queries):
        query = random.choice(test_queries)
        try:
            async with session.post(f"{base_url}/ask",
                json={"text": query}) as response:
                result = await response.json()
                console.print(f"Client {client_id} - Query {i+1}: {result}")
                await asyncio.sleep(random.uniform(0.5, 2.0))
        except Exception as e:
            console.print(f"[red]Error from client {client_id}:[/] {str(e)}")

async def main():
    num_clients = 5
    queries_per_client = 3

    async with aiohttp.ClientSession() as session:
        tasks = [
            simulate_client(session, i, queries_per_client)
            for i in range(num_clients)
        ]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())