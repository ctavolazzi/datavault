#!/usr/bin/env python3

import requests

def fetch_pokemon_data(pokemon_id):
    """Fetches Pokemon data using PokeAPI"""
    try:
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(f"Error fetching Pokemon data: {str(e)}")
        return None