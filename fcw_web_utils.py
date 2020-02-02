import requests

base_url = 'https://freecivweb.org'

def fetch_games():
    url = f'{base_url}/game/list/json'
    response = requests.get(url=url)
    return response.json()

def get_game_list():
    active_ports = {}
    for game in fetch_games():
        active_ports[game['port']] = game
    return active_ports
