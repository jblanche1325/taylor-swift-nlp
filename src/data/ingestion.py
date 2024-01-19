import os
import sys
from src.exception import CustomException
from src.logger import logging
from dotenv import load_dotenv

import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from bs4 import BeautifulSoup
import requests
from dataclasses import dataclass

load_dotenv()

@dataclass
class DataIngestionConfig:
    raw_data_path: str=os.path.join('raw', 'taylor_swift_raw.csv')

class DataIngestion:
    def __init__(self) -> None:
        self.ingestion_config = DataIngestionConfig()

    def spotipy_credentials(self):
        '''
        This function pulls the user's key and secret and creates
        the connection to the Spotify API.
        '''

        try:
            spotify_key = os.getenv('SPOTIFY_KEY')
            spotify_secret = os.getenv('SPOTIFY_SECRET')

            client_credentials_manager = SpotifyClientCredentials(client_id=spotify_key, 
                                                                client_secret=spotify_secret)

            sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

            logging.info('Spotipy API successfully connected')

            return sp
        
        except Exception as e:
            raise CustomException(e, sys)
        
    def get_albums_and_songs(self):
        '''
        This function uses the Spotify API to pull and store the album name,
        song titles, and song uri.
        '''

        try:
            tswift_uri = '06HL4z0CvFAxyc27GXpf02' # Pulled from Taylor Swift Spotify page

            sp = self.spotipy_credentials()

            tswift_albums = sp.artist_albums(tswift_uri)
            name = []
            uri = []
            for i in tswift_albums['items']:
                name.append(i['name'])
                uri.append(i['uri'])

            logging.info('Successfully pulled album names')

            song_name = []
            song_uri = []
            album = []
            count = 0
            for j in uri:
                tracks = sp.album_tracks(j)   
                for i in tracks['items']:
                    album.append(name[count])
                    song_name.append(i['name'])
                    song_uri.append(i['uri'])
                count += 1

            logging.info('Successfully pulled song names and uris')

            return album, song_name, song_uri, sp

        except Exception as e:
            raise CustomException(e, sys)
    
    def get_audio_features(self):
        '''
        This function uses the Spotify API to pull audio features
        about each song.
        '''

        try:
            album, song_name, song_uri, sp = self.get_albums_and_songs()

            acoustic = []
            dance = []
            energy = []
            instrumental = []
            liveness = []
            loudness = []
            speech = []
            tempo = []
            valence = []
            popularity = []

            for i in song_uri:
                feat = sp.audio_features(i)[0]
                acoustic.append(feat['acousticness'])
                dance.append(feat['danceability'])
                energy.append(feat['energy'])
                speech.append(feat['speechiness'])
                instrumental.append(feat['instrumentalness'])
                loudness.append(feat['loudness'])
                tempo.append(feat['tempo'])
                liveness.append(feat['liveness'])
                valence.append(feat['valence'])
                popu = sp.track(i)
                popularity.append(popu['popularity'])

            ts_audiofeatures = pd.DataFrame({'name': song_name,
                                             'album': album,
                                             'dance': dance,
                                             'acoustic': acoustic,
                                             'energy': energy,
                                             'instrumental': instrumental,
                                             'liveness': liveness,
                                             'loudness': loudness,
                                             'speech': speech,
                                             'tempo': tempo,
                                             'valence': valence,
                                             'popularity': popularity
            })

            logging.info('Stored audio features into DataFrame')
            return ts_audiofeatures

        except Exception as e:
            raise CustomException(e, sys)
        
if __name__ == '__main__':
    obj = DataIngestion()
    ts_audiofeatures = obj.get_audio_features()

    print(ts_audiofeatures.head())