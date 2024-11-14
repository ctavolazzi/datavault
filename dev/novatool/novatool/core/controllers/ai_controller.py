from novatool.core.hubs.ai_hub import AIHub
from rich.console import Console
import asyncio

class AIController:
    def __init__(self):
        self.hub = AIHub()
        self.console = Console()

    async def start(self):
        """Start the AI system"""
        # Start background tasks
        self.health_task = asyncio.create_task(self.hub.update_health_metrics())
        self.console.print(self.hub.display_status())

    async def stop(self):
        """Stop background tasks"""
        if hasattr(self, 'health_task'):
            self.health_task.cancel()
            try:
                await self.health_task
            except asyncio.CancelledError:
                pass

    async def process_query(self, query: str) -> str:
        """Process a query through the hub"""
        return await self.hub.process_query(query)

    def show_status(self):
        """Show current hub status"""
        self.console.print(self.hub.display_status())