import uvicorn
from novatool.server.ai_server import AIServer
import asyncio

async def main():
    server = AIServer()
    await server.start()
    server.setup_routes()

    config = uvicorn.Config(
        server.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())