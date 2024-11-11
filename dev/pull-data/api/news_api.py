from flask import current_app
import requests
import os
from dotenv import load_dotenv

class NewsAPI:
    def __init__(self):
        env_path = "/Users/ctavolazzi/Code/datavault/dev/.env"
        load_dotenv(env_path)
        self.api_key = os.getenv('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2"

    def _make_request(self, endpoint, params=None):
        if params is None:
            params = {}
        params['apiKey'] = self.api_key

        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"News API error: {str(e)}")
            return None

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

    def get_sources(self, category=None, language='en', country='us'):
        params = {
            'language': language,
            'country': country
        }
        if category:
            params['category'] = category
        return self._make_request('top-headlines/sources', params)