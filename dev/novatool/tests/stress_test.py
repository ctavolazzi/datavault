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

class AISystemTester:
    def __init__(self):
        self.console = Console()
        self.test_queries = [
            "What is artificial intelligence?",
            "Explain machine learning",
            "How do neural networks work?",
            "What is deep learning?",
            "Explain natural language processing"
        ]

    async def run_all_tests(self):
        """Run all test queries and display results"""
        self.console.print("[bold green]Starting AI System Tests[/]")

        async with aiohttp.ClientSession() as session:
            results = []

            # Run each test query
            for i, query in enumerate(self.test_queries, 1):
                self.console.print(f"\n[cyan]Running Query {i}/{len(self.test_queries)}[/]")
                self.console.print(f"Query: {query}")

                try:
                    # Send query to server
                    async with session.post(
                        'http://localhost:8000/ask',
                        json={"text": query}
                    ) as response:
                        result = await response.json()
                        if "error" in result:
                            raise Exception(result["error"])
                        results.append({
                            "query": query,
                            "status": "success",
                            "response": result
                        })
                        self.console.print(f"[green]✓ Query completed[/]")
                        self.console.print(f"Response: {result['response'][:100]}...")
                except Exception as e:
                    results.append({
                        "query": query,
                        "status": "failed",
                        "error": str(e)
                    })
                    self.console.print(f"[red]✗ Query failed: {str(e)}[/]")

                # Wait between queries
                await asyncio.sleep(2)

            # Display final results
            self.console.print("\n[bold cyan]Test Results Summary[/]")
            successful = len([r for r in results if r["status"] == "success"])
            self.console.print(f"Total Queries: {len(self.test_queries)}")
            self.console.print(f"Successful: [green]{successful}[/]")
            self.console.print(f"Failed: [red]{len(results) - successful}[/]")

def run_server_process():
    """Function to run in separate process"""
    try:
        from novatool.server.ai_server import AIServer
        import uvicorn
        from fastapi import FastAPI
        from pydantic import BaseModel
        import ollama

        print("[DEBUG] Starting server process...")

        class Query(BaseModel):
            text: str

        app = FastAPI()

        # Get available models
        available_models = AIConfig.get_available_models(AIService.OLLAMA)
        primary_model = AIConfig.get_model(AIService.OLLAMA)
        fallback_model = AIConfig.get_fallback_model(AIService.OLLAMA)

        print(f"[DEBUG] Available models: {available_models}")
        print(f"[DEBUG] Primary model: {primary_model}")
        print(f"[DEBUG] Fallback model: {fallback_model}")

        # Select model to use
        model_to_use = primary_model if primary_model in available_models else fallback_model
        print(f"[DEBUG] Using model: {model_to_use}")

        @app.on_event("startup")
        async def startup_event():
            print("[DEBUG] Application startup complete")

        @app.get("/test")
        async def test():
            return {"status": "ok"}

        @app.post("/ask")
        async def ask(query: Query):
            try:
                start_time = time.time()
                print(f"[DEBUG] Starting query processing: {query.text}")

                response = ollama.chat(
                    model=model_to_use,
                    messages=[
                        {
                            'role': 'system',
                            'content': '''You are a helpful AI assistant. You must follow these rules strictly:
                            1. Provide EXACTLY three words in your response
                            2. Separate words with single spaces
                            3. No punctuation
                            4. No additional explanation
                            Example good response: "machines learn patterns"
                            '''
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

                # Validate response format
                if word_count != 3:
                    print(f"[WARNING] Response contains {word_count} words instead of 3: '{result}'")
                    # Optionally, we could retry here

                print(f"[DEBUG] Query completed in {processing_time:.2f}s")
                print(f"[DEBUG] Word count: {word_count}/3")
                print(f"[DEBUG] Raw response: '{result}'")

                return {
                    "response": result,
                    "metadata": {
                        "processing_time": processing_time,
                        "word_count": word_count,
                        "model_used": model_to_use,
                        "valid_format": word_count == 3
                    }
                }
            except Exception as e:
                print(f"[ERROR] Query processing failed: {e}")
                print(traceback.format_exc())
                return {"error": str(e)}

        print("[DEBUG] Starting uvicorn on port 8000...")

        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
    except Exception as e:
        print(f"[ERROR] Server startup failed: {e}")
        traceback.print_exc()
        sys.exit(1)

def wait_for_server(timeout: int = 30) -> bool:
    """Wait for server to be ready"""
    console = Console()
    start_time = time.time()
    attempt = 0

    console.print("[yellow]Waiting for server startup[/]")

    while time.time() - start_time < timeout:
        try:
            # Reduce logging noise by only showing every 5th attempt
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

if __name__ == "__main__":
    try:
        # Start server process
        server_process = multiprocessing.Process(target=run_server_process)
        server_process.start()
        print(f"[DEBUG] Started server process with PID: {server_process.pid}")

        # Wait for server to be ready
        if not wait_for_server(timeout=30):
            print("[red]Server failed to start[/]")
            server_process.terminate()
            sys.exit(1)

        # Run tests
        tester = AISystemTester()
        asyncio.run(tester.run_all_tests())

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        print(traceback.format_exc())
    finally:
        # Clean shutdown
        if 'server_process' in locals() and server_process.is_alive():
            print("Terminating server process...")
            server_process.terminate()
            server_process.join(timeout=5)