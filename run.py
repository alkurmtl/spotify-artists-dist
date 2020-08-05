import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
from _collections import deque
from telegram.ext import Updater

LIMIT = 20
VISITED_LIMIT = 1000

credentials_file = open('credentials.txt', 'r')
client_id, client_secret = credentials_file.read().split()
auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

telegram_token = credentials_file.read()
updater = Updater(token=telegram_token, use_context=True)
credentials_file.close()

class Searcher:

    def __init__(self):
        self.color = dict()
        self.parent = dict()
        self.parent_song = dict()

    @classmethod
    def get_all_artists_on_feats(cls, artist_id):
        cur_offset_albums = 0
        res = set()
        while True:
            albums = sp.artist_albums(artist_id, offset=cur_offset_albums, limit=LIMIT)
            if len(albums['items']) == 0:
                break
            album_ids = []
            for album in albums['items']:
                album_ids.append(album['id'])
            albums = sp.albums(album_ids)
            for album in albums['albums']:
                for song in album['tracks']['items']:
                    has_needed = False
                    for artist in song['artists']:
                        if artist['id'] == artist_id:
                            has_needed = True
                            break
                    if not has_needed:
                        continue
                    for artist in song['artists']:
                        if artist['id'] != artist_id:
                            res.add((artist['name'], artist['id'], song['name']))
            cur_offset_albums += LIMIT
        return res

    def __recover_path(self, artist_name):
        path = []
        current_artist = artist_name
        while self.parent[current_artist] is not None:
            path.append(current_artist + ', ' + self.parent[current_artist] + ': ' + self.parent_song[current_artist])
            current_artist = self.parent[current_artist]
        return path

    def bfs(self, start_artist, end_artist):
        self.color = dict()
        self.parent = dict()
        self.parent_song = dict()
        start_artist_name = sp.artist(start_artist)['name']
        end_artist_name = sp.artist(end_artist)['name']
        q = deque()
        q.append((start_artist_name, start_artist))
        q.append((end_artist_name, end_artist))
        self.color[start_artist_name] = 0
        self.color[end_artist_name] = 1
        self.parent[start_artist_name] = None
        self.parent[end_artist_name] = None
        artist_1 = ''
        path_1 = []
        artist_2 = ''
        path_2 = []
        visited = 0
        while len(q) > 0:
            current_artist_name, current_artist_id = q.popleft()
            visited += 1
            print(current_artist_name)
            if visited >= VISITED_LIMIT:
                return ['Path not found']
            feats = Searcher.get_all_artists_on_feats(current_artist_id)
            found = False
            for to_artist_name, to_artist_id, song_name in feats:
                if to_artist_name not in self.parent:
                    q.append((to_artist_name, to_artist_id))
                    self.color[to_artist_name] = self.color[current_artist_name]
                    self.parent[to_artist_name] = current_artist_name
                    self.parent_song[to_artist_name] = song_name
                elif self.color[to_artist_name] == (self.color[current_artist_name] ^ 1):
                    artist_1 = current_artist_name
                    artist_2 = to_artist_name
                    path_1.append(current_artist_name + ', ' + to_artist_name + ': ' + song_name)
                    found = True
                    break
            if found:
                break
        path_1 = path_1 + self.__recover_path(artist_1)
        path_2 = self.__recover_path(artist_2)
        path = []
        if path_1[-1].find(end_artist_name) != -1:
            path_2.reverse()
            path = path_2 + path_1
        else:
            path_1.reverse()
            path = path_1 + path_2
        return path


artist1_name = 'Aikko'
artist2_name = 'Скриптонит'
res = sp.search(q=artist1_name, type='artist')
start_artist = res['artists']['items'][0]['id']
res = sp.search(q=artist2_name, type='artist')
end_artist = res['artists']['items'][0]['id']
searcher = Searcher()
path = searcher.bfs(start_artist, end_artist)
print('\n' + sp.artist(start_artist)['name'] + ' to ' + sp.artist(end_artist)['name'])
for s in path:
    print(s)







#print(res)
#with open('/mnt/c/Users/Alexander.LAPTOP-L2LI4V4F/Desktop/res.json', 'w') as outfile:
#    json.dump(res, outfile)
