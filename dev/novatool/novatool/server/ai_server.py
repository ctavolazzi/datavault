from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import asyncio
from ..core.hubs.ai_hub import AIHub
from ..ui.hud import AIHUD
from rich.console import Console
import random
import time
import psutil
from ..utils.ai_config import AIService
import uuid

class Query(BaseModel):
    text: str
    priority: Optional[int] = 1
    context: Optional[dict] = {}

class AIServer:
    def __init__(self):
        self.app = FastAPI(title="AI System Server")
        self.hub = AIHub()
        self.console = Console()
        self.hud = AIHUD(self.console)
        self.query_queue = asyncio.Queue()
        self.is_processing = False
        self.startup_time = time.time()
        self.messages = []

    def setup_routes(self):
        """Set up all FastAPI routes with detailed logging"""
        self.hud.add_message("[yellow]📡 Configuring API endpoints...[/]")

        # Print existing routes
        print("\n[DEBUG] Existing routes before setup:")
        for route in self.app.routes:
            print(f"  • {route.methods} {route.path}")

        @self.app.post("/ask")
        async def ask(query: Query):
            query_id = str(uuid.uuid4())[:8]
            self.hud.add_message(f"[cyan]📝 New Query ({query_id}):[/]")
            self.hud.add_message(f"  • Text: {query.text[:50]}{'...' if len(query.text) > 50 else ''}")
            self.hud.add_message(f"  • Priority: {query.priority}")

            await self.query_queue.put(query)
            position = self.query_queue.qsize()

            self.hud.add_message(f"[blue]📊 Queue Status:[/]")
            self.hud.add_message(f"  • Position: {position}")
            self.hud.add_message(f"  • Total Queued: {position}")

            return {"status": "queued", "position": position, "query_id": query_id}

        @self.app.get("/status")
        async def status():
            print("[DEBUG] Status endpoint called")
            return {
                "status": "ok",
                "is_processing": self.is_processing,
                "queue_size": self.query_queue.qsize()
            }

        @self.app.post("/model")
        async def set_model(model: str):
            self.hud.add_message(f"[yellow]🔄 Model change requested:[/]")
            self.hud.add_message(f"  • New Model: {model}")
            self.hud.add_message(f"  • Current Model: {self.hub.get_current_model()}")

            success = await self.set_model(model)
            status = "success" if success else "failed"

            self.hud.add_message(
                f"[{'green' if success else 'red'}]{'✓' if success else '❌'} Model change {status}[/]"
            )
            return {"success": success, "current_model": self.hub.get_current_model()}

        @self.app.on_event("startup")
        async def startup_event():
            self.hud.add_message("[yellow]🎬 Server startup initiated[/]")
            await self.start()

        @self.app.on_event("shutdown")
        async def shutdown_event():
            self.hud.add_message("[yellow]🛑 Server shutdown initiated...[/]")
            self.hud.add_message("  • Stopping background tasks")
            self.hud.add_message("  • Cleaning up resources")
            await self.stop()
            self.hud.add_message("[green]✓ Shutdown complete[/]")

        self.hud.add_message("[green]✓ API routes configured successfully[/]")
        self.hud.add_message("  • POST /ask - Submit queries")
        self.hud.add_message("  • GET /status - Check system status")
        self.hud.add_message("  • POST /model - Change AI model")

        # Print routes after setup
        print("\n[DEBUG] Routes after setup:")
        for route in self.app.routes:
            print(f"  • {route.methods} {route.path}")

    async def add_message(self, message: str):
        """Add a message to both the server and HUD"""
        self.messages.append(message)
        self.hud.add_message(message)

    async def start(self):
        """Start the server and HUD with detailed status information"""
        try:
            # Initialize HUD first
            self.hud.start()
            await self.add_message("[bold green]🚀 Initializing AI System[/]")

            # AI Hub initialization
            await self.add_message("[yellow]⚡ Initializing AI Hub[/]")
            await self.hub.start()
            await self.add_message("[green]✓ AI Hub initialized[/]")

            # Start background tasks
            await self.add_message("[yellow]🔄 Starting background tasks[/]")
            asyncio.create_task(self.process_queue())
            asyncio.create_task(self._update_hud())
            await self.add_message("[green]✓ Background tasks started[/]")

            # System health check
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            await self.add_message("[yellow]🔍 System Health Check[/]")
            await self.add_message(f"  • CPU: [{'green' if cpu_usage < 70 else 'red'}]{cpu_usage}%[/]")
            await self.add_message(f"  • RAM: [{'green' if memory_usage < 70 else 'red'}]{memory_usage}%[/]")

            # Update initial stats
            self.hud.update({
                "cpu": cpu_usage,
                "memory": memory_usage,
                "api": 100.0,
                "messages": len(self.messages),
                "tokens": 0,
                "context_length": 0,
                "queue_size": 0,
                "processed": 0,
                "is_processing": False
            })

            startup_duration = time.time() - self.startup_time
            await self.add_message(f"[green]✨ System ready ({startup_duration:.2f}s)[/]")

        except Exception as e:
            await self.add_message(f"[bold red]❌ Startup Error: {str(e)}[/]")
            raise

    async def stop(self):
        """Stop the server and cleanup"""
        self.hud.stop()
        await self.hub.stop()

    async def process_queue(self):
        """Background task to process queries"""
        while True:
            if not self.query_queue.empty():
                query = await self.query_queue.get()
                self.is_processing = True

                try:
                    # Update HUD with processing status and API at 100%
                    stats = {
                        "api": 100.0,  # API is busy
                        "is_processing": True
                    }
                    self.hud.update(stats)
                    self.hud.add_message(f"[cyan]Processing:[/] {query.text}")

                    # Process the query
                    response = await self.hub.process_query(query.text)

                    # Get updated stats from hub
                    stats = {
                        "messages": len(self.hub.memory_stats['messages']),
                        "tokens": self.hub.memory_stats['tokens'],
                        "context_length": self.hub.memory_stats['context_length'],
                        "queue_size": self.query_queue.qsize(),
                        "processed": self.hub.memory_stats['total_processed'],
                        "is_processing": False,
                        "cpu": psutil.Process().cpu_percent(),
                        "memory": psutil.Process().memory_percent(),
                        "api": 0.0  # API is idle again
                    }
                    self.hud.update(stats)

                except Exception as e:
                    self.hud.add_message(f"[red]Error:[/] {str(e)}")
                finally:
                    self.is_processing = False
                    self.query_queue.task_done()

    async def _update_hud(self):
        """Background task to update HUD metrics"""
        process = psutil.Process()

        while True:
            try:
                # Get CPU and memory metrics
                cpu_percent = process.cpu_percent()
                memory_percent = process.memory_percent()

                # Combine all stats
                combined_stats = {
                    "cpu": float(cpu_percent),
                    "memory": float(memory_percent),
                    "api": 100.0 if self.is_processing else 0.0,  # Reversed logic
                    "messages": len(self.hub.memory_stats.get("messages", [])),
                    "tokens": self.hub.memory_stats.get("tokens", 0),
                    "context_length": self.hub.memory_stats.get("context_length", 0),
                    "queue_size": self.query_queue.qsize(),
                    "processed": self.hub.memory_stats.get("total_processed", 0),
                    "is_processing": self.is_processing
                }

                # Update HUD with combined stats
                self.hud.update(combined_stats)
                await asyncio.sleep(0.25)

            except Exception as e:
                self.console.print(f"[red]Error updating HUD metrics: {str(e)}[/]")
                await asyncio.sleep(1.0)

    async def set_model(self, model_name: str) -> bool:
        """Change AI model"""
        if self.hub.set_model(model_name):
            self.hud.add_message(f"[green]Switched to model:[/] {model_name}")
            return True
        self.hud.add_message(f"[red]Invalid model:[/] {model_name}")
        return False