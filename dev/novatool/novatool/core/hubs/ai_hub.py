from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime
from rich.panel import Panel
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box
import time
import asyncio
from enum import Enum
from novatool.ui.ai_components import (
    AIThinkingSpinner,
    AIEmotiveResponse,
    AIStatusIndicator,
    AIModelInfo,
    AISystemHealth,
    AITaskProgress,
    AIMemoryStats,
    create_ai_timer_box,
    create_ai_success_box,
    create_ai_error_box
)
import random
import psutil
import os
from novatool.utils.ai_config import AIConfig, AIService

class AIHubStatus(Enum):
    """Hub operational states"""
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    LEARNING = "learning"

@dataclass
class AITask:
    """Represents a task in the AI system"""
    id: str
    type: str
    priority: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

class AIHub:
    """Central hub for AI operations and monitoring"""

    def __init__(self, service: AIService = AIService.OLLAMA):
        """Initialize the AI Hub"""
        # Core initialization
        self.status = AIHubStatus.READY
        self.start_time = time.time()
        self._running = False
        self.process = psutil.Process()

        # Initialize metrics
        self.metrics = {
            "cpu": 0.0,
            "memory": 0.0,
            "api": 100.0
        }

        # Initialize memory tracking
        self.messages = []  # Store actual messages
        self.memory_stats = {
            "messages": [],  # List of message objects
            "tokens": 0,     # Total tokens processed
            "context_length": 0,  # Current context length
            "total_processed": 0  # Total queries processed
        }

        # Session tracking
        self.session_data = {
            "total_requests": 0,
            "successful_responses": 0,
            "errors": 0,
            "start_time": time.time()
        }

        self.service = service
        self.current_model = AIConfig.get_model(service)
        self.fallback_model = AIConfig.get_fallback_model(service)
        self.available_models = AIConfig.get_available_models(service)

    async def start(self):
        """Start the AI Hub and background tasks"""
        self._running = True
        self._update_task = asyncio.create_task(self._update_metrics())
        return self

    async def stop(self):
        """Stop the AI Hub and cleanup"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

    async def _update_metrics(self):
        """Background task to update metrics"""
        while self._running:
            try:
                # Ensure we're sending numeric values
                self.metrics.update({
                    "cpu": float(self.process.cpu_percent(interval=0.1)),
                    "memory": float(self.process.memory_percent()),
                    "api": 100.0 if self.status == AIHubStatus.READY else 0.0
                })
                await asyncio.sleep(0.25)
            except Exception as e:
                print(f"Error updating metrics: {e}")
                self.metrics.update({
                    "cpu": 0.0,
                    "memory": 0.0,
                    "api": 0.0
                })
                await asyncio.sleep(1.0)

    async def process_query(self, query: str) -> str:
        """Process a query and update stats"""
        try:
            # Add query to messages
            self.messages.append({"role": "user", "content": query})

            # Update memory stats
            self.memory_stats["messages"] = self.messages
            self.memory_stats["total_processed"] += 1

            # Simulate token counting (replace with actual token counting)
            estimated_tokens = len(query.split())
            self.memory_stats["tokens"] += estimated_tokens
            self.memory_stats["context_length"] = len(self.messages)

            # Process query (replace with actual processing)
            response = f"Processed: {query}"

            # Add response to messages
            self.messages.append({"role": "assistant", "content": response})

            return response

        except Exception as e:
            print(f"Error processing query: {str(e)}")
            raise

    def display_status(self) -> Panel:
        """Generate comprehensive status display"""
        # Create the main grid layout
        layout = Table.grid(padding=(0, 1))

        # Status header with session time
        uptime = time.time() - self.start_time
        header = f"Session: {uptime:.1f}s | Status: {self.status.value.title()}"
        layout.add_row(Panel(header, title="🤖 AI System Monitor", border_style="blue"))

        # System metrics table
        metrics_table = Table(title="System Metrics", show_header=True, box=box.SIMPLE)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        metrics_table.add_column("Status", style="yellow")

        # Add metrics rows with proper formatting
        metrics_table.add_row("CPU", f"{self.metrics['cpu']:.1f}%",
            "Normal" if self.metrics['cpu'] < 80 else "High")
        metrics_table.add_row("Memory", f"{self.metrics['memory']:.1f}%",
            "Normal" if self.metrics['memory'] < 80 else "High")
        metrics_table.add_row("API", f"{self.metrics['api']:.1f}%",
            "Online" if self.metrics['api'] > 90 else "Degraded")

        # Health monitor panel
        health_status = Table.grid()
        health_status.add_row("System:", "Online", style="green")
        health_status.add_row("Queue:", self.status.value.title(), style="cyan")
        health_status.add_row("Load:", "Normal" if self.metrics['cpu'] < 80 else "High",
            style="green" if self.metrics['cpu'] < 80 else "red")

        health_panel = Panel(health_status, title="❤️ Health Monitor", border_style="blue")

        # Memory stats with more detail
        memory_table = Table.grid()
        memory_table.add_row(f"Messages: {self.memory_stats['messages']}")
        memory_table.add_row(f"Tokens: {self.memory_stats['tokens']}")
        memory_table.add_row(f"Total Processed: {self.memory_stats['total_processed']}")
        memory_panel = Panel(memory_table, title="📊 Memory Stats", border_style="blue")

        # Add all components to main layout
        layout.add_row(
            Table.grid()
            .add_row(metrics_table, health_panel)
            .add_row(memory_panel)
        )

        return Panel(layout, box=box.ROUNDED, border_style="blue")

    def _create_task(self, task_type: str, metadata: Any) -> AITask:
        """Create and register a new task"""
        task = AITask(
            id=f"task_{len(self.tasks)}",
            type=task_type,
            priority=1,
            status="pending",
            created_at=datetime.now(),
            metadata=metadata
        )
        self.tasks.append(task)
        return task

    def _update_stats(self, success: bool):
        """Update hub statistics"""
        self.session_data["total_requests"] += 1
        if success:
            self.session_data["successful_responses"] += 1
        else:
            self.session_data["errors"] += 1

    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage"""
        total = self.session_data["total_requests"]
        if total == 0:
            return 100.0
        return (self.session_data["successful_responses"] / total) * 100

    async def monitor_resources(self):
        """Monitor system resources"""
        while True:
            # Update resource usage (mock values for now)
            self.resources["CPU"] = 50.0
            self.resources["Memory"] = 30.0
            self.resources["Model Load"] = 25.0
            await asyncio.sleep(1)

    async def update_health_metrics(self):
        """Update system health metrics periodically"""
        while True:
            try:
                # Get real CPU and memory metrics
                cpu_percent = self.process.cpu_percent()
                memory_percent = self.process.memory_percent()

                # Update metrics with actual values
                self.metrics.update({
                    "cpu": float(cpu_percent),
                    "memory": float(memory_percent),
                    "api": 100.0 if self.status == AIHubStatus.READY else 50.0
                })

                # Short sleep to prevent excessive updates
                await asyncio.sleep(0.25)

            except Exception as e:
                print(f"Error updating metrics: {str(e)}")
                await asyncio.sleep(1.0)

    def _call_ollama(self, query: str) -> str:
        """Make actual Ollama call (to be implemented)"""
        # Simulate response for now
        return f"This is a simulated response to: {query}"

    def set_model(self, model_name: str) -> bool:
        """Set current model if available"""
        if model_name in self.available_models:
            self.current_model = model_name
            return True
        return False

    def get_current_model(self) -> str:
        """Get currently active model"""
        return self.current_model

# Example usage:
async def main():
    hub = AIHub()

    # Start resource monitoring
    asyncio.create_task(hub.monitor_resources())

    # Show live status
    with Live(hub.display_status(), refresh_per_second=4) as live:
        response = await hub.process_query("What is the meaning of life?")
        live.update(hub.display_status())

        # Show final response
        print(f"\nResponse: {response}")

if __name__ == "__main__":
    asyncio.run(main())