import asyncio
import aiohttp
import random
from rich.console import Console
import multiprocessing
import sys
from pathlib import Path
import time
import requests
import traceback
import signal
import os
import ollama
from novatool.utils.ai_config import AIConfig, AIService
import json

class AITelephoneTester:
    def __init__(self):
        self.console = Console()
        self.initial_prompt = "What is artificial intelligence?"
        self.num_rounds = 10
        self.log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                                    "telephone_game.log")

        print(f"[DEBUG] Writing logs to: {self.log_file}")

        # Clear log file at start
        with open(self.log_file, "w") as f:
            f.write("")  # Clear file

        # Log startup immediately
        self.log_startup()

    def log_query_start(self, query: str):
        """Log when a query starts processing"""
        log_entry = {
            "query": query,
            "timestamp": time.time()
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            f.flush()

    def log_response(self, round_num: int, message: str, processing_time: float):
        """Log round information to file"""
        log_entry = {
            "round": round_num,
            "message": message,
            "processing_time": processing_time,
            "word_count": len(message.split()),
            "timestamp": time.time()
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            f.flush()

    def log_startup(self):
        """Log when the game starts"""
        log_entry = {
            "event": "startup",
            "type": "game_start",
            "timestamp": time.time(),
            "message": "🎮 AI Telephone Game Starting!"
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            f.flush()  # Force write to disk

    def log_server_ready(self):
        """Log when server is ready"""
        log_entry = {
            "event": "startup",
            "type": "server_ready",
            "timestamp": time.time(),
            "message": "🚀 Server Ready - Starting Game!"
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            f.flush()

    async def run_telephone_game(self):
        """Run telephone game test and display results"""
        # Log startup first
        self.log_startup()

        self.console.print("[bold green]Starting AI Telephone Game[/]")
        current_message = self.initial_prompt

        async with aiohttp.ClientSession() as session:
            for i in range(self.num_rounds):
                self.console.print(f"\n[cyan]Round {i+1}/{self.num_rounds}[/]")
                self.console.print(f"Input: {current_message}")

                try:
                    # Log that we're starting a query
                    self.log_query_start(current_message)

                    start_time = time.time()

                    # Send message to server
                    async with session.post(
                        'http://localhost:8000/ask',
                        json={"text": current_message}
                    ) as response:
                        result = await response.json()
                        if "error" in result:
                            raise Exception(result["error"])

                        processing_time = time.time() - start_time
                        response_text = result.get('response', '')

                        # Log the response
                        self.log_response(i + 1, response_text, processing_time)

                        # Update current message for next round
                        current_message = response_text

                        self.console.print(f"[green]✓ Response received: {response_text}[/]")

                except Exception as e:
                    self.console.print(f"[red]✗ Error: {str(e)}[/]")
                    traceback.print_exc()
                    break

                # Wait between rounds
                await asyncio.sleep(2)

def wait_for_server(timeout: int = 30) -> bool:
    """Wait for server to be ready"""
    console = Console()
    start_time = time.time()
    attempt = 0

    console.print("[yellow]Waiting for server startup[/]")

    while time.time() - start_time < timeout:
        try:
            if attempt % 5 == 0:
                print(f"[DEBUG] Connection attempt {attempt + 1}...")

            response = requests.get('http://localhost:8000/test', timeout=1)
            if response.status_code == 200:
                console.print(f"[green]✓ Server ready after {attempt + 1} attempts ({int(time.time() - start_time)}s)[/]")
                return True
        except requests.RequestException:
            attempt += 1
            time.sleep(0.5)

    console.print("[red]✗ Server failed to start within timeout period[/]")
    return False

def start_server():
    """Start the FastAPI server"""
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel

    app = FastAPI()

    class Query(BaseModel):
        text: str

    @app.get("/test")
    async def test():
        return {"status": "ok"}

    @app.post("/ask")
    async def ask(query: Query):
        try:
            start_time = time.time()
            print(f"[DEBUG] Starting query processing: {query.text}")

            response = ollama.chat(
                model='nemotron-mini',  # or your chosen model
                messages=[
                    {
                        'role': 'system',
                        'content': '''You are playing a game of telephone. Take the input and rephrase it in your own words.
                        Keep responses concise but natural. Aim for 5-10 words.'''
                    },
                    {
                        'role': 'user',
                        'content': query.text
                    }
                ]
            )

            processing_time = time.time() - start_time
            result = response['message']['content'].strip()
            word_count = len(result.split())

            print(f"[DEBUG] Query completed in {processing_time:.2f}s")
            print(f"[DEBUG] Word count: {word_count}")
            print(f"[DEBUG] Raw response: '{result}'")

            return {
                "response": result,
                "metadata": {
                    "processing_time": processing_time,
                    "word_count": word_count,
                    "model_used": 'nemotron-mini'
                }
            }
        except Exception as e:
            print(f"[ERROR] Query processing failed: {e}")
            print(traceback.format_exc())
            return {"error": str(e)}

    print("[DEBUG] Starting server process...")
    uvicorn.run(app, host="127.0.0.1", port=8000)

async def main():
    tester = AITelephoneTester()
    await tester.run_telephone_game()

if __name__ == "__main__":
    server_process = None

    try:
        # Create tester instance (this will log startup)
        tester = AITelephoneTester()

        # Start the server
        server_process = multiprocessing.Process(target=start_server)
        server_process.start()
        print(f"[DEBUG] Started server process with PID: {server_process.pid}")

        # Wait for server to be ready
        if not wait_for_server():
            raise Exception("Server failed to start")

        # Log that server is ready
        tester.log_server_ready()

        # Run the telephone game
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\nReceived interrupt signal...")
    finally:
        print("Terminating server process...")
        if server_process:
            server_process.terminate()
            server_process.join()