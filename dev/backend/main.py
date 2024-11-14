from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from dotenv import load_dotenv
import os
from apis.news_api import NewsAPI
from datetime import datetime
from typing import List
import json
from pathlib import Path
import hashlib
import asyncio

# Import cache-related modules
from utils.caching.cache_service import CacheService
from utils.caching.config import CacheConfig
from utils.caching.exceptions import CacheError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # SvelteKit default dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize NewsAPI
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
if not NEWSAPI_KEY:
    raise Exception("NEWSAPI_KEY not found in environment variables")

news_api = NewsAPI(NEWSAPI_KEY)

class SearchQuery(BaseModel):
    query: str

class SearchLog(BaseModel):
    user_id: str
    query: str
    timestamp: datetime

# In-memory storage (temporary solution)
search_logs: List[SearchLog] = []

def get_cache_path():
    # Create cache directory structure if it doesn't exist
    base_path = Path("cache")
    base_path.mkdir(exist_ok=True)
    return base_path

def cache_response(query: str, response_data: dict, cache_type: str = "search"):
    """Cache API response to filesystem"""
    try:
        # Create hash of query for filename
        query_hash = hashlib.md5(query.encode()).hexdigest()

        # Create dated folder structure: cache/2024/03/14/
        today = datetime.now()
        cache_dir = get_cache_path() / str(today.year) / str(today.month) / str(today.day) / cache_type
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Save response with metadata
        cache_data = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "response": response_data
        }

        # Save to file: cache/2024/03/14/search/query_hash.json
        cache_file = cache_dir / f"{query_hash}.json"
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        logger.info(f"Cached response for query: {query}")
    except Exception as e:
        logger.error(f"Failed to cache response: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/search")
async def search_news(search_query: SearchQuery):
    try:
        logger.info(f"Searching for: {search_query.query}")

        # Use existing cache service instance
        cache_service = app.state.cache_service

        # Try to get from cache first
        try:
            cached_response = await cache_service.get(search_query.query)
            if cached_response:
                logger.info(f"Returning cached response for: {search_query.query}")
                return JSONResponse(content=cached_response)
        except Exception as e:
            logger.warning(f"Cache error: {str(e)}")

        # If not in cache, fetch from NewsAPI
        logger.info(f"Cache miss - fetching from NewsAPI: {search_query.query}")
        response = news_api.search_everything(search_query.query)

        # Cache in background
        asyncio.create_task(cache_service.cache_response_async(search_query.query, response))

        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch news")

@app.get("/api/top-headlines")
async def get_top_headlines():
    try:
        logger.info("Getting top headlines for us")

        # Try to get from cache first
        cache_service = app.state.cache_service
        cached_headlines = await cache_service.get("top_headlines")

        if cached_headlines:
            logger.info("📦 Returning cached top headlines")
            return JSONResponse(content=cached_headlines)

        # If not in cache, fetch from API
        logger.info("🌐 Cache miss - fetching fresh headlines from API")
        headlines = news_api.get_top_headlines(country='us')

        # Cache in background
        asyncio.create_task(cache_service.cache_response_async("top_headlines", headlines))

        return JSONResponse(content=headlines)

    except Exception as e:
        logger.error(f"Failed to get top headlines: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch headlines")

@app.post("/api/log_search")
async def log_search(log: SearchLog):
    try:
        logger.info(f"Search logged: {log.query} for user {log.user_id}")
        search_logs.append(log)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to log search: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log search")

@app.get("/api/search_history/{user_id}")
async def get_search_history(user_id: str):
    try:
        user_logs = [log for log in search_logs if log.user_id == user_id]
        return user_logs
    except Exception as e:
        logger.error(f"Failed to retrieve search history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch search history")

@app.on_event("startup")
async def startup_event():
    """Initialize app with top headlines"""
    try:
        logger.info("Loading initial top headlines")
        cache_config = CacheConfig(base_dir=Path("cache"))

        # Get cache service instance
        app.state.cache_service = await CacheService.get_instance(cache_config)

        # Try to get from cache first
        cached_headlines = await app.state.cache_service.get("top_headlines")
        if cached_headlines:
            logger.info("Using cached top headlines")
            app.state.top_headlines = cached_headlines
            return

        # If not in cache, fetch and cache
        headlines = news_api.get_top_headlines(country='us')
        await app.state.cache_service.cache_response_async("top_headlines", headlines)
        logger.info("Cached initial top headlines")
        app.state.top_headlines = headlines

    except Exception as e:
        logger.error(f"Failed to load initial headlines: {str(e)}")
        app.state.top_headlines = {"articles": []}

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources"""
    try:
        if hasattr(app.state, 'cache_service'):
            await app.state.cache_service.cleanup()
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache performance statistics"""
    stats = await app.state.cache_service.get_stats()
    return {"status": "success", "data": stats}

@app.delete("/api/cache/clear")
async def clear_cache():
    """Clear all cache data"""
    try:
        await app.state.cache_service.clear_all()
        return {"status": "success", "message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@app.get("/api/cache/health")
async def cache_health():
    """Get detailed cache health metrics"""
    try:
        stats = await app.state.cache_service.get_stats()
        health_check = await app.state.cache_service.health_check()

        return {
            "status": "success",
            "data": {
                "stats": stats,
                "health": health_check,
                "status": "healthy" if health_check["all_systems_ok"] else "degraded"
            }
        }
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cache health check failed")

@app.post("/api/cache/optimize")
async def optimize_cache():
    """Trigger cache optimization"""
    try:
        result = await app.state.cache_service.optimize()
        return {
            "status": "success",
            "data": {
                "optimized_entries": result["optimized"],
                "space_saved": result["space_saved"],
                "duration": result["duration"]
            }
        }
    except Exception as e:
        logger.error(f"Cache optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cache optimization failed")

@app.get("/api/cache/size")
async def get_cache_size():
    """Get current cache size and limits"""
    try:
        size_info = await app.state.cache_service.get_size_info()
        return {
            "status": "success",
            "data": {
                "current_size": size_info["current_size"],
                "max_size": size_info["max_size"],
                "usage_percent": size_info["usage_percent"],
                "items_count": size_info["items_count"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get cache size: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get cache size")

@app.post("/api/cache/preload")
async def preload_common_searches():
    """Preload cache with common searches"""
    try:
        common_searches = [
            "technology",
            "business",
            "science",
            "health",
            "sports"
        ]

        results = await app.state.cache_service.preload_searches(common_searches)
        return {
            "status": "success",
            "data": {
                "preloaded": results["preloaded"],
                "failed": results["failed"],
                "duration": results["duration"]
            }
        }
    except Exception as e:
        logger.error(f"Cache preload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cache preload failed")