import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
import time

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from novatool.core.hubs.ai_hub import AIHub, AIHubStatus
from novatool.core.controllers.ai_controller import AIController
from novatool.ui.hud import AIHUD

async def test_ai_system():
    console = Console()
    controller = AIController()
    hud = AIHUD(console)

    # Test queries
    test_queries = [
        "What is quantum computing?",
        "How do neural networks work?",
        "Explain the concept of recursion"
    ]

    # Start the controller and HUD
    await controller.start()
    hud.start(len(test_queries))

    try:
        for i, query in enumerate(test_queries, 1):
            # Update query display
            hud.set_query(query, i)
            hud.stats = controller.hub.memory_stats  # Sync stats

            # Process query
            controller.hub.status = AIHubStatus.BUSY
            hud.update(controller.hub)

            # Simulate processing
            await asyncio.sleep(1.5)

            response = await controller.process_query(query)
            hud.set_response(response, 1.5)

            # Update status
            controller.hub.status = AIHubStatus.READY
            hud.update(controller.hub)

            await asyncio.sleep(2)  # Show result briefly

    finally:
        hud.stop()
        await controller.stop()
        console.print("\n[bold green]✨ Test Complete![/]\n")

if __name__ == "__main__":
    asyncio.run(test_ai_system())