import os
import requests


def get_spotify_token() -> str:
    """Refresh and return a Spotify access token using the stored refresh token."""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    refresh_token = os.getenv('SPOTIFY_REFRESH_TOKEN')

    if not refresh_token:
        print("No SPOTIFY_REFRESH_TOKEN set. Run token_script.sh to get one.")
        return ""

    r = requests.post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
    })

    data = r.json()
    if 'access_token' not in data:
        print(f"Spotify token refresh failed: {data}")
        return ""

    return data['access_token']
