import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
from _collections import deque

LIMIT = 20
DIST_LIMIT = 10

dist = dict()
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


def bfs(start_artist, end_artist):
    start_artist_name = sp.artist(start_artist)['name']
    q = deque()
    q.append((start_artist_name, start_artist))
    dist[start_artist] = 0
    parent[start_artist_name] = None
    while len(q) > 0:
        current_artist_name, current_artist_id = q.popleft()
        if current_artist_name == 'Pyrokinesis':
            kek = 0
        print(current_artist_name)
        if dist[current_artist_id] >= DIST_LIMIT:
            return ['Dist >= 10']
        feats = get_all_artists_on_feats(current_artist_id)
        found = False
        for to_artist_name, to_artist_id in feats:
            if to_artist_name not in parent:
                q.append((to_artist_name, to_artist_id))
                dist[to_artist_id] = dist[current_artist_id] + 1
                parent[to_artist_name] = current_artist_name
                if to_artist_id == end_artist:
                    found = True
                    break
        if found:
            break
    path = []
    current_artist = sp.artist(end_artist)['name']
    while current_artist is not None:
        path.append(current_artist)
        current_artist = parent[current_artist]
    path.reverse()
    return path


credentials_file = open('credentials.txt', 'r')
client_id, client_secret = credentials_file.read().split()
credentials_file.close()
auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

path = bfs('1gCOYbJNUa1LBVO5rlx0jB', '0Cm90jv892OeEegB3ELmvN')
print(path)
#res = get_all_artists_on_feats('5rXtHvb8jMNgmSX7Khd77x')
#print(res)
#res = sp.albums(['1Tmh5qT7B3jFfypXFaCqgt', '7491SDsfObnnywNTtuaXAW'])
#with open('/mnt/c/Users/Alexander.LAPTOP-L2LI4V4F/Desktop/res.json', 'w') as outfile:
#    json.dump(res, outfile)
