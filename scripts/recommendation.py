import os
import asyncio
import requests # pip install scikit-learn and numpy
from dotenv import load_dotenv
import spotify_data
import pandas as pd
import pickle
import json

os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
load_dotenv()

# GOAL: Take in spotify playlist and recommend 5 movies according to 
# - Amount of songs in a movie that match it
# - Most similar genre

# 1: get_playlist_data: takes in a spotify playlist ID (from spotify_data.py) and returns it as a dict in the form:
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

# 4. process movie data
    
    
# 5. soundtrack_recommend(): Function that 
# - takes in the tracklist and movies objects
# - for each movie, count how many tracks from the playlist appear in the movie's soundtrack -- either by:
#      - matching song names
#      - matching artist names
#   - put each movie with a match in a list
#   - keep track of which movies have the most overlap with the playlist

# 6.  genre_recommend(): Function that
# - takes in the spotify playlist dict
# - records each genre of every track in a list.
# - looks for movies in TMDB that contains the the most genre matches as the ones in the playlist


if __name__ == "__main__":

# Spotify Data (spotify_data):
    
    # Import ids and tracks from spotify_data
    """playlist_id = spotify_data.playlist_id
    tracklist = spotify_data.tracks

    # Extract artist and genre lists
    playlist_dict = get_playlist_data(playlist_id)
    artist_list = []
    genre_list = []

    for track in playlist_dict:
        artist_list.append(track["artists"])
        genre_list.append(track["genres"])"""

# Movie data (movie_data):
    # Arist genre data
    with open("../data/spotify-artist-genre-results.pkl", 'rb') as data:
        genre_data = pickle.load(data)
    artist_genres_df = pd.DataFrame(genre_data)
    artist_genres_df = artist_genres_df[0].apply(json.loads).apply(pd.Series)

    # Soundtrack data
        # Spotify soundtrack search data
    with open("../data/spotify-soundtrack-results.pkl", 'rb') as data:
        soundtrack_data = pickle.load(data)
    spotify_soundtrack_df = pd.DataFrame(soundtrack_data)
    spotify_soundtrack_df[0] = spotify_soundtrack_df[0].replace({'No track found' : '{}', pd.NA: '{}'}) # if no track or pd.NA ==> {}
    spotify_soundtrack_df = spotify_soundtrack_df[0].apply(json.loads).apply(pd.Series)

        # IMDB soundtrack data
    imdb_df = pd.read_csv('../data/sound_track_imdb_top_250_movie_tv_series.csv')
    imdb_df.drop(columns=['written_performed_by', 'conducted_by', 'libretto_by', 'under_license_from', 'Unnamed: 0'], inplace=True)
    imdb_df['performed_by'] = imdb_df['performed_by'].fillna("nan").astype(str)
    imdb_df = imdb_df.reset_index(drop=True)
    
        # Merge Spotify and IMDB soundtrack data
    imdb_spotify_soundtracks_df = pd.concat([spotify_soundtrack_df, imdb_df], axis=1)
    imdb_spotify_soundtracks_df.drop(columns=['year', 'written_by', 'composed_by', 'lyrics_by', 'music_by','courtesy_of'], inplace=True)
    imdb_spotify_soundtracks_df.dropna(subset=['spotify_song', 'spotify_artist', 'spotify_id'], inplace=True)
    imdb_spotify_soundtracks_df.reset_index(drop=True, inplace=True)

    # Combine soundtrack and artist/genre data 
    imdb_spotify_soundtracks_genres = pd.concat([artist_genres_df, imdb_spotify_soundtracks_df], axis=1)
    imdb_spotify_soundtracks_genres = imdb_spotify_soundtracks_genres.drop(columns = ['spotify_artist1'])
    imdb_spotify_soundtracks_genres.reset_index(drop=True, inplace=True)
    desired_order = ['name', 'song_name', 'performed_by', 'spotify_song', 'spotify_artist', 'spotify_id', 'spotify_album']
    imdb_spotify_soundtracks_genres = imdb_spotify_soundtracks_genres[desired_order]

    # logging tools to test
    """imdb_spotify_soundtracks_genres.to_csv('artist_genre_soundtrack.csv', index=False, mode='a')
    print(spotify_soundtrack_df.columns)
    print(imdb_df.columns)
    print(imdb_spotify_soundtracks_genres.columns)"""
