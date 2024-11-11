import os
import requests
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class NewsAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"

    def _make_request(self, endpoint, params=None):
        if params is None:
            params = {}
        params['apiKey'] = self.api_key

        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"News API error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_top_headlines(self, country='us', category=None, q=None):
        params = {'country': country}
        if category:
            params['category'] = category
        if q:
            params['q'] = q
        return self._make_request('top-headlines', params)

    def search_everything(self, query, sort_by='publishedAt', language='en'):
        params = {
            'q': query,
            'sortBy': sort_by,
            'language': language
        }
        return self._make_request('everything', params)