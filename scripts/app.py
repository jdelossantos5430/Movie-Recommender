import os
import asyncio
import requests # pip install scikit-learn and numpy
from dotenv import load_dotenv
from spotify_data import get_playlist # change these to function names when u get them
from movie_data import get_kaggle_data

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# GOAL: Take in spotify playlist and recommend 5 movies according to 
# - Amount of songs in a movie that match it
# - Most similar genre

# HELPER FUNCTIONS: 1. get_playlist_data(), 2. get_genres(), 3. process_artist_list(), 4. get_kaggle_data()

# 1: get_playlist_data: function that takes in a spotify playlist ID (from spotify_data.py) and returns it in a dict in the form:
# {
#  "track_id": {
#    "name": "Track Name",
#    "artists": ["Artist A", "Artist B"],
#   "genres": ["pop", "indie rock"] }

def get_playlist_data(playlist_object):
    items = playlist_object["tracks"]["items"]
    tracks = {}

    for item in items:
        track = item["track"]
        track_id = track["id"]
        track_name = track["name"]

        # process artist arrays
        track_artists_data = track["artists"] # array of track artists' data
        artist_names, genres = process_artist_list(track_artists_data) # get only the names (list) and genres (list) of each artist 

        tracks[track_id] = {"name": track_name, "artists": artist_names, "genres": genres}
    return tracks

# 2. get_genres(): This will probably be in the spotify data file but just make it here for now to test the other functions
def get_genres(artist_id):
    api_key = os.getenv("SPOTIFY_API_KEY")
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["genres"] # returns a list of genres
    else:
        return []

# 3. process_artist_list(): Take in artist arrays and return artist_names (list) and genres(list)
def process_artist_list(artist_array):
    artist_names = []
    genres = set() # array of genre arrays, 1 for each artist
    for artist in artist_array:
        artist_names.append(artist["name"])
        artist_genres = get_genres(artist["id"])
        genres.update(artist_genres)
    return artist_names, list(genres)

# 4. process data from kaggle csv to use in recommender function (This would be in movie_data.py but just write it here to test the functions)
# Should return an object in the form 
#{
#    "title": ...,
#    "songs" {
#        "song name": ["artists", ...]
#    }
#}

def get_kaggle_data():
    with open ('../sound_track_imdb/Movie-Recommender/sound_track_imdb_top_250_movie_tv_series.csv', "r") as file:
        content = file.read()
    
    
# 5. soundtrack_reccomend(): Function that 
# - takes in the spotify playlist dict and movies objects
# - for each movie, count how many tracks from the playlist appear in the movie's soundtrack -- either by:
#      - matching song names
#      - matching artist names
#   - put each movie with a match in a list
#   - keep track of which movies have the most overlap with the playlist

# 6.  genre_recommend(): Function that
# - takes in the spotify playlist dict
# - records each genre of every track in a list.
# - looks for movies in TMDB that contains the the most genre matches as the ones in the playlist




# Get playlist data with playlist id from spotify_data.py
playlist_dict = get_playlist_data(get_playlist)



