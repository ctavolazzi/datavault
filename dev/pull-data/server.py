from flask import Flask, render_template, jsonify, request
from api.news_api import NewsAPI
from api import poke_api
import random

app = Flask(__name__)
news_client = NewsAPI()

@app.route('/')
def home():
    try:
        # Get random Pokemon
        pokemon_id = random.randint(1, 151)
        pokemon_data = poke_api.fetch_pokemon_data(pokemon_id)

        # Get latest news
        news_data = news_client.get_top_headlines()
        sources = news_client.get_sources()

        return render_template('dashboard.html',
                             pokemon_data=pokemon_data,
                             news_data=news_data,
                             sources=sources)
    except Exception as e:
        app.logger.error(f"Error loading homepage: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/api/news/search')
def search_news():
    query = request.args.get('q', '')
    category = request.args.get('category')
    source = request.args.get('source')

    if source:
        return jsonify(news_client.get_top_headlines(sources=source))
    elif category:
        return jsonify(news_client.get_top_headlines(category=category))
    else:
        return jsonify(news_client.search_everything(query))

@app.route('/api/news/sources')
def get_news_sources():
    category = request.args.get('category')
    return jsonify(news_client.get_sources(category=category))

@app.route('/api/pokemon/search')
def search_pokemon():
    query = request.args.get('query', '').lower()
    try:
        pokemon_data = poke_api.fetch_pokemon_data(query)
        return jsonify(pokemon_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/news/refresh')
def refresh_news():
    try:
        news_data = news_client.get_top_headlines()
        return jsonify(news_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)