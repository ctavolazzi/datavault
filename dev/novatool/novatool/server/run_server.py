import asyncio
import uvicorn
from fastapi import FastAPI
from .ai_server import AIServer
import signal
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_server():
    try:
        server = AIServer()

        # Start the HUD first
        server.hud.start()
        server.hud.add_message("[yellow]🚀 Starting server...[/]")

        # Setup routes
        server.setup_routes()
        server.hud.add_message("[green]✓ Routes configured[/]")

        # Start server components
        await server.start()

        # Configure uvicorn
        config = uvicorn.Config(
            server.app,
            host="127.0.0.1",
            port=8000,
            log_level="error",
            reload=False
        )

        server.hud.add_message("[green]✓ Server ready to accept connections[/]")

        # Start uvicorn
        server_instance = uvicorn.Server(config)
        await server_instance.serve()

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == "__main__":
    import uvicorn

    server = AIServer()
    server.setup_routes()

    uvicorn.run(
        server.app,
        host="127.0.0.1",
        port=8000,
        log_level="error"
    )