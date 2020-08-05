import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
from _collections import deque

LIMIT = 20
VISITED_LIMIT = 1000

color = dict()
parent = dict()


def get_all_artists_on_feats(artist_id):
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
                        res.add((artist['name'], artist['id']))
        cur_offset_albums += LIMIT
    return res


def recover_path(artist_name):
    path = []
    current_artist = artist_name
    while current_artist is not None:
        path.append(current_artist)
        current_artist = parent[current_artist]
    return path


def bfs(start_artist, end_artist):
    start_artist_name = sp.artist(start_artist)['name']
    end_artist_name = sp.artist(end_artist)['name']
    q = deque()
    q.append((start_artist_name, start_artist))
    q.append((end_artist_name, end_artist))
    color[start_artist_name] = 0
    color[end_artist_name] = 1
    parent[start_artist_name] = None
    parent[end_artist_name] = None
    artist_1 = ''
    artist_2 = ''
    visited = 0
    while len(q) > 0:
        current_artist_name, current_artist_id = q.popleft()
        visited += 1
        print(current_artist_name)
        if visited >= VISITED_LIMIT:
            return ['Path not found']
        if current_artist_name == 'Automatikk':
            kek = '2JrBKNalGY7zqWDVx3BIFc'
        feats = get_all_artists_on_feats(current_artist_id)
        found = False
        for to_artist_name, to_artist_id in feats:
            if to_artist_name not in parent:
                q.append((to_artist_name, to_artist_id))
                color[to_artist_name] = color[current_artist_name]
                parent[to_artist_name] = current_artist_name
            elif color[to_artist_name] == (color[current_artist_name] ^ 1):
                artist_1 = current_artist_name
                artist_2 = to_artist_name
                found = True
                break
        if found:
            break
    path_1 = recover_path(artist_1)
    path_2 = recover_path(artist_2)
    path = []
    if path_1[-1] == end_artist_name:
        path_2.reverse()
        path = path_2 + path_1
    else:
        path_1.reverse()
        path = path_1 + path_2
    return path


credentials_file = open('credentials.txt', 'r')
client_id, client_secret = credentials_file.read().split()
credentials_file.close()
auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

path = bfs('2O7iILP4xoejqge6ntRhgR', '1F8usyx5PbYGWxf0bwdXwA')
print(path)
#res = get_all_artists_on_feats('5rXtHvb8jMNgmSX7Khd77x')
#print(res)
#res = sp.albums(['1Tmh5qT7B3jFfypXFaCqgt', '7491SDsfObnnywNTtuaXAW'])
#with open('/mnt/c/Users/Alexander.LAPTOP-L2LI4V4F/Desktop/res.json', 'w') as outfile:
#    json.dump(res, outfile)
