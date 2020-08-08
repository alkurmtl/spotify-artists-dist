import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
from _collections import deque
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import logging

LIMIT = 20
VISITED_LIMIT = 200

logging.basicConfig(filename='log.txt', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

credentials_file = open('credentials.txt', 'r')
spotify_credentials, telegram_token = credentials_file.read().splitlines()
client_id, client_secret = spotify_credentials.split()
auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

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
        artists = set()
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
                        if artist['id'] != artist_id and artist['name'] not in artists:
                            res.add((artist['name'], artist['id'], song['name']))
                            artists.add(artist['name'])
            cur_offset_albums += LIMIT
        return res

    def __recover_path(self, artist_name):
        path = []
        current_artist = artist_name
        while self.parent[current_artist] is not None:
            path.append([current_artist, self.parent[current_artist], self.parent_song[current_artist]])
            current_artist = self.parent[current_artist]
        return path

    def bfs(self, start_artist, end_artist, update, context):
        self.color = dict()
        self.parent = dict()
        self.parent_song = dict()
        start_artist_name = sp.artist(start_artist)['name']
        end_artist_name = sp.artist(end_artist)['name']
        logging.info('starting search for ' + telegram_user_to_str(update.effective_user) + '. Artists are ' +
                     start_artist_name + ' ' + end_artist_name)
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
        found = False
        while len(q) > 0:
            current_artist_name, current_artist_id = q.popleft()
            visited += 1
            logging.info('processing ' + current_artist_name + ' in search for ' +
                         telegram_user_to_str(update.effective_user))
            if visited >= VISITED_LIMIT:
                logging.info('Finished search for ' +
                             telegram_user_to_str(update.effective_user) + ': not found')
                return [['Not found', 'Not found', 'Not found']]
            if visited % 10 == 0:
                context.bot.send_message(chat_id=update.effective_chat.id, text='Обработали ' +
                                                                            str(visited) + ' исполнителей')
            feats = Searcher.get_all_artists_on_feats(current_artist_id)
            for to_artist_name, to_artist_id, song_name in feats:
                if to_artist_name not in self.parent:
                    q.append((to_artist_name, to_artist_id))
                    self.color[to_artist_name] = self.color[current_artist_name]
                    self.parent[to_artist_name] = current_artist_name
                    self.parent_song[to_artist_name] = song_name
                elif self.color[to_artist_name] == (self.color[current_artist_name] ^ 1):
                    artist_1 = current_artist_name
                    artist_2 = to_artist_name
                    path_1.append([current_artist_name, to_artist_name, song_name])
                    logging.info('Finished search for ' +
                                 telegram_user_to_str(update.effective_user) + ': found')
                    found = True
                    break
            if found:
                break
        if not found:
            logging.info('Finished search for ' +
                         telegram_user_to_str(update.effective_user) + ': not found')
            return [['Not found', 'Not found', 'Not found']]
        path_1 = path_1 + self.__recover_path(artist_1)
        path_2 = self.__recover_path(artist_2)
        path = []
        if path_1[-1][0] == end_artist_name or path_1[-1][1] == end_artist_name:
            path_2.reverse()
            path = path_2 + path_1
        else:
            path_1.reverse()
            path = path_1 + path_2
        if path[0][0] != start_artist_name:
            path[0][0], path[0][1] = path[0][1], path[0][0]
        for i in range(1, len(path)):
            if path[i - 1][1] != path[i][0]:
                path[i][0], path[i][1] = path[i][1], path[i][0]
        return path


def telegram_user_to_str(user):
    res = user.first_name
    if user.last_name is not None:
        res += ' ' + user.last_name
    if user.username is not None:
        res += ' (' + user.username + ')'
    return res


def start(update, context):
    logging.info('start from ' + telegram_user_to_str(update.effective_user))
    context.bot.send_message(chat_id=update.effective_chat.id, text='Напишите двух исполнителей '
                                                                    'отдельным сообщением в формате:'
                                                                    '\nПервый исполнитель'
                                                                    '\nВторой исполнитель')


def get_artist_id(query):
    try:
        res = sp.artist(query)
        artist = res['id']
    except Exception:
        res = sp.search(q=query, type='artist')
        if len(res['artists']['items']) == 0:
            return None
        artist = res['artists']['items'][0]['id']
    return artist


def search(update, context):
    logging.info('message from ' + telegram_user_to_str(update.effective_user) + ':\n' + update.message.text)
    artists = update.message.text.splitlines()
    if len(artists) != 2:
        context.bot.send_message(chat_id=update.effective_chat.id, text='В вашем сообщении должно быть две строки')
        logging.info('rejected search query from ' + telegram_user_to_str(update.effective_user) +
                     ' because message consists of not two lines')
        return
    start_artist = get_artist_id(artists[0])
    if start_artist is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Первый исполнитель не найден')
        logging.info('rejected search query from ' + telegram_user_to_str(update.effective_user) +
                     ' because first artist isn\'t found')
    end_artist = get_artist_id(artists[1])
    if end_artist is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Второй исполнитель не найден')
        logging.info('rejected search query from ' + telegram_user_to_str(update.effective_user) +
                     ' because first artist isn\'t found')
    if start_artist == end_artist:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Исполнители совпадают')
        logging.info('rejected search query from ' + telegram_user_to_str(update.effective_user) +
                     ' because artist are the same')
        return
    searcher = Searcher()
    path = searcher.bfs(start_artist, end_artist, update, context)
    path_message = ''
    for song in path:
        path_message += song[0] + ', ' + song[1] + ': ' + song[2] + '\n'
    context.bot.send_message(chat_id=update.effective_chat.id, text=path_message,
                             reply_to_message_id=update.message.message_id)


updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), search))
updater.start_polling()
print('Started')







#res = sp.artist('https://spotipy.readthedocs.io/en/2.13.0/')
#with open('/mnt/c/Users/Alexander.LAPTOP-L2LI4V4F/Desktop/res.json', 'w') as outfile:
#    json.dump(res, outfile)
