from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from dotenv import load_dotenv
import os
from apis.news_api import NewsAPI
from datetime import datetime
from typing import List

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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/search")
async def search_news(search_query: SearchQuery):
    try:
        logger.info(f"Searching for: {search_query.query}")
        return news_api.search_everything(search_query.query)
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch news")

@app.get("/api/top-headlines")
async def get_top_headlines(country: str = 'us', category: str = None):
    try:
        logger.info(f"Getting top headlines for {country}")
        return news_api.get_top_headlines(country=country, category=category)
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