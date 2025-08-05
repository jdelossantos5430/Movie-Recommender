import os
import re
import asyncio
import requests # pip install scikit-learn and numpy
from dotenv import load_dotenv
import spotify_data
import pandas as pd
import pickle
import json
import heapq

os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
load_dotenv()

# GOAL: Take in spotify playlist and recommend 5 movies according to 
# - Amount of songs in a movie that match it
# - Most similar genre

# Process Spotify data
sp = getattr(spotify_data, "sp", None)
if sp is None:
    raise Exception("spotify_data.py must define `sp` at top-level.")

def get_playlist_data(playlist_ID):
    """ takes in a spotify playlist ID and returns it as a dict in the form:
 {
  "track_id": {
    "name": "Track Name",
    "artists": ["Artist A", "Artist B"],
    "genres": ["pop", "indie rock"] }

   :param playlist_ID: Spotify Playlist ID (from spotify_data.py)
   :type playlist_ID: String
    """
    tracks = {}
    playlist_object = spotify_data.sp.playlist(playlist_ID)
    items = playlist_object["tracks"]["items"]
    next_page = playlist_object['tracks']['next']

    while next_page:
        playlist_object = spotify_data.sp.next(playlist_object['tracks'])
        items.extend(playlist_object['items'])
        next_page = playlist_object['next']

    for item in items:
        track = item["track"]
        track_id = track["id"]
        track_name = track["name"]

        # process artist arrays
        track_artists_data = track["artists"] # array of track artists' data
        artist_names, genres = process_artist_list(track_artists_data) # get only the names (list) and genres (list) of each artist 

        tracks[track_id] = {"name": track_name, "artists": artist_names, "genres": genres}
    return tracks

def get_genres(artist_id):
    # This will probably be in the spotify data file but just make it here for now to test the other functions
    api_key = os.getenv("SPOTIFY_API_KEY")
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["genres"] # returns a list of genres
    else:
        return []
def process_artist_list(artist_array):
    """Take in artist arrays and return artist_names (list) and genres(list)
    
    :param artist_array: Array of artists
    :type artist_array: Array
    """
    artist_names = []
    genres = set() # array of genre arrays, 1 for each artist
    for artist in artist_array:
        artist_names.append(artist["name"])
        artist_data = sp.artist(artist["id"])
        artist_genres = artist_data.get("genres", [])
        genres.update(artist_genres)
    return artist_names, list(genres)

def process_movie_data():
    """Run movie_data.ipynb first"""
    # Artist genre data
    with open("../data/spotify-artist-genre-results.pkl", 'rb') as data:
        genre_data = pickle.load(data)
    artist_genres_df = pd.DataFrame(genre_data)
    artist_genres_df = artist_genres_df[0].apply(json.loads).apply(pd.Series)

    # Soundtrack data
    with open("../data/spotify-soundtrack-results.pkl", 'rb') as data:
        soundtrack_data = pickle.load(data)
    spotify_soundtrack_df = pd.DataFrame(soundtrack_data)
    spotify_soundtrack_df[0] = spotify_soundtrack_df[0].replace({'No track found' : '{}', pd.NA: '{}'})
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

    imdb_spotify_soundtracks_genres.to_csv('imdb_spotify_soundtracks_genres.csv', index=False, mode='a')

def soundtrack_recommend(playlist_data, movie_soundtracks):
    matchlist = {}       
    match_songs = {}     

    for index, movie_track in movie_soundtracks.iterrows():
        movie_song = movie_track['song_name']
        movie_artist = movie_track['performed_by']

        if not (isinstance(movie_song, str) and isinstance(movie_artist, str)):
            continue
        
        movie_song_clean = clean_song_title(movie_song)
        movie_song_norm = normalize_string(movie_song_clean)
        movie_artist_norm = normalize_string(movie_artist)

        for playlist_track in playlist_data.values():
            if not (playlist_track['name'] and all(playlist_track['artists'])):
                continue
            playlist_song_clean = clean_song_title(playlist_track['name'])
            playlist_song_norm = normalize_string(playlist_song_clean)
            playlist_artists_norm = [normalize_string(artist) for artist in playlist_track['artists']]

            song_match = (playlist_song_norm in movie_song_norm) or (movie_song_norm in playlist_song_norm)
            artist_match = any(playlist_artist in movie_artist_norm for playlist_artist in playlist_artists_norm)

            if song_match and artist_match:
                movie_name = movie_track['name']
                matchlist[movie_name] = matchlist.get(movie_name, 0) + 1
                match_songs.setdefault(movie_name, set()).add(playlist_track['name'])
                break

    top_5_movies = heapq.nlargest(5, matchlist.items(), key=lambda item: item[1])

    for movie, count in top_5_movies:
        songs = ", ".join(match_songs.get(movie, []))
        print(f"- {movie}: {count} matching song(s) — Matches: {songs}\n")

    return top_5_movies

def normalize_string(s):
    s = s.lower()
    s = re.sub(r'\b(and|the|of|a|an)\b', '', s)  # remove common stopwords
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def clean_track_name(name):
    return re.sub(r'\s*-\s*(remaster|live|edit|version|bonus track).*', '', name, flags=re.I)

def clean_song_title(title):
    suffixes = [
        r'\s*-\s*single version',
        r'\s*-\s*remaster(ed)?',
        r'\s*-\s*live',
        r'\s*\(live\)',
        r'\s*\(remaster(ed)?\)',
    ]
    for suffix in suffixes:
        title = re.sub(suffix, '', title, flags=re.IGNORECASE)
    return title.strip()

def main():
    if not os.path.exists("imdb_spotify_soundtracks_genres.csv"):
        process_movie_data()
    else:
        global imdb_spotify_soundtracks_genres
        imdb_spotify_soundtracks_genres = pd.read_csv("imdb_spotify_soundtracks_genres.csv")
    playlist_url = input("Enter a Spotify playlist URL: ").strip()
    playlist_id = spotify_data.extract_playlist_id(playlist_url)
    playlist_data = get_playlist_data(playlist_id)

    print(f"Recommended Movies by soundtrack:\n")
    soundtrack_recommend(playlist_data, imdb_spotify_soundtracks_genres)

if __name__ == "__main__":
    main()
