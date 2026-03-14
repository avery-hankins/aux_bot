#!/bin/bash
# First-time Spotify auth: opens browser, you paste the redirect URL, and it saves the refresh token to .env

# Parse .env (handles spaces around = and quoted values)
while IFS= read -r line; do
    line="${line%%#*}"  # strip comments
    [[ -z "$line" ]] && continue
    key="${line%%=*}"
    key="${key%% *}"
    val="${line#*=}"
    val="${val# }"
    val="${val%\"}"
    val="${val#\"}"
    export "$key=$val"
done < .env

open "https://accounts.spotify.com/authorize?response_type=code&client_id=${SPOTIFY_CLIENT_ID}&scope=user-library-read%20playlist-modify-private&redirect_uri=$(python3 -c 'import urllib.parse; print(urllib.parse.quote("'"${SPOTIFY_REDIRECT_URI}"'"))')"

echo "Paste the full redirect URL:"
read -r REDIRECT_URL

CODE=$(echo "$REDIRECT_URL" | sed "s/.*code=//")

RESPONSE=$(curl -s -X POST "https://accounts.spotify.com/api/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=authorization_code&code=$CODE&redirect_uri=$SPOTIFY_REDIRECT_URI&client_id=$SPOTIFY_CLIENT_ID&client_secret=$SPOTIFY_CLIENT_SECRET")

REFRESH_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('refresh_token',''))")
ACCESS_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

if [ -z "$REFRESH_TOKEN" ]; then
    echo "Error: no refresh token in response"
    echo "$RESPONSE"
    exit 1
fi

# Update .env with the refresh token
sed -i '' "s|^SPOTIFY_REFRESH_TOKEN.*|SPOTIFY_REFRESH_TOKEN = \"$REFRESH_TOKEN\"|" .env

echo "Refresh token saved to .env"
echo "Access token (for testing): $ACCESS_TOKEN"
