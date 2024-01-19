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
        
    def scrape_lyrics(self, artistname, songname):
        '''
        This function scrapes song lyrics from Genius.com 
        using BeautifulSoup
        '''

        try:
            # Clean up artist and song names        
            artistname2 = str(artistname.replace(' ','-')) if ' ' in artistname else str(artistname)
            songname2 = str(songname.replace(' ','-')) if ' ' in songname else str(songname)
            songname2 = str(songname2.replace('(','')) if '(' in songname2 else str(songname2)
            songname2 = str(songname2.replace(')','')) if ')' in songname2 else str(songname2)
            songname2 = str(songname2.replace("'",'')) if "'" in songname2 else str(songname2)
            # Get html from page and find lyrics
            page = requests.get('https://genius.com/'+ artistname2 + '-' + songname2 + '-' + 'lyrics')
            html = BeautifulSoup(page.text, 'html.parser')
            lyrics1 = html.find("div", class_="lyrics")
            lyrics2 = html.find("div", class_="Lyrics__Container-sc-1ynbvzw-1 kUgSbL")
            if lyrics1:
                lyrics = lyrics1.get_text()
            elif lyrics2:
                lyrics = lyrics2.get_text()
            elif lyrics1 == lyrics2 == None:
                lyrics = None

            return lyrics
        
        except Exception as e:
            raise CustomException(e, sys)
        
    def lyrics_onto_frame(self, df, artist_name):
        '''
        This function uses scrape_lyrics() to loop through
        each song and pull the lyrics into a dataframe.
        '''
        try:
            for i, x in enumerate(df['name']):
                test = self.scrape_lyrics(artist_name, x)
                df.loc[i, 'lyrics'] = test

            logging.info('Joined lyrics to audio features dataframe')

            return df
        
        except Exception as e:
            raise CustomException(e, sys)
        
if __name__ == '__main__':
    # Initiate DataIngestion()
    obj = DataIngestion()
    # Get Audio Features and store into ts_audiofeatures
    ts_audiofeatures = obj.get_audio_features()
    # Get lyrics and join to ts_audiofeatures and store into ts_df
    ts_df = obj.lyrics_onto_frame(ts_audiofeatures, 'Taylor Swift')
    
    print(ts_df.head())