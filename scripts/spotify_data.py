import re
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Define the scope for necessary permissions
scope = "playlist-read-private playlist-read-collaborative user-library-read"

# Authenticate using Authorization Code Flow
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="9ea7760f9a604525951307f4ca2d4693",
    client_secret="6b604ddbe3484962a3211b42718de8a2",
    redirect_uri="http://127.0.0.1:8000/callback",
    scope=scope
))

# Function to extract playlist ID from Spotify playlist URL
def extract_playlist_id(url):
    match = re.search(r"playlist/([a-zA-Z0-9]{22})", url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid Spotify playlist URL.")

# Function to get tracks from playlist
def get_playlist_tracks(playlist_id):
    tracks = []
    results = sp.playlist_items(playlist_id)
    tracks.extend(results['items'])

    # Paginate through all items
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    return tracks

# Function to get genres for each track (via artist)
def get_track_genres(track_item):
    artist_id = track_item['track']['artists'][0]['id']
    artist_info = sp.artist(artist_id)
    return artist_info.get('genres', [])

# Main execution
if __name__ == "__main__":
    playlist_url = input("Enter a Spotify playlist URL: ").strip()
    try:
        playlist_id = extract_playlist_id(playlist_url)
        print(f"Extracted Playlist ID: {playlist_id}")

        print("Fetching tracks...")
        tracks = get_playlist_tracks(playlist_id)
        print(f"Found {len(tracks)} tracks.")

        for idx, item in enumerate(tracks):
            track = item['track']
            name = track['name']
            artist = track['artists'][0]['name']
            genres = get_track_genres(item)
            print(f"{idx + 1}. {name} by {artist} | Genres: {', '.join(genres) if genres else 'Unknown'}")

    except Exception as e:
        print(f"Error: {e}")

