#!/usr/bin/env python3

import os
import shutil

def create_dashboard(pokemon_data, news_data):
    """Creates the combined dashboard HTML"""
    # Load template
    template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'dashboard.html')
    with open(template_path, 'r') as f:
        template = f.read()

    # Format template with data
    html_content = template.format(
        pokemon_name=pokemon_data['name'].title(),
        pokemon_sprite=pokemon_data['sprites']['front_default'],
        pokemon_sprite_shiny=pokemon_data['sprites']['front_shiny'],
        pokemon_types=''.join([f'<span class="type {t["type"]["name"]}">{t["type"]["name"]}</span>'
                          for t in pokemon_data['types']]),
        pokemon_stats=''.join([f'<div class="stat-bar"><span>{s["stat"]["name"]}</span>'
                         f'<div class="bar" style="width: {s["base_stat"]}%">{s["base_stat"]}</div></div>'
                         for s in pokemon_data['stats']]),
        news_articles=''.join([create_news_card(article) for article in news_data.get('articles', [])])
    )

    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)

    # Copy CSS file to output
    css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'css', 'combined.css')
    shutil.copy2(css_path, 'output/combined.css')

    # Write HTML file
    with open('output/dashboard.html', 'w') as f:
        f.write(html_content)

def create_news_card(article):
    """Creates HTML for a single news card"""
    return f'''
        <div class="news-card">
            <img src="{article.get('urlToImage', '')}" onerror="this.style.display='none'">
            <h3>{article.get('title', '')}</h3>
            <p>{article.get('description', '')}</p>
            <a href="{article.get('url', '')}" target="_blank">Read More</a>
        </div>
    '''
