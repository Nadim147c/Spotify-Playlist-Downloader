from __future__ import unicode_literals
from unicodedata import name
from spotipy.oauth2 import SpotifyClientCredentials
from tkinter import Tk, filedialog
from dotenv import load_dotenv
import urllib
import youtube_dl
import spotipy
import eyed3
import time
import os

load_dotenv()


CLIENT_CREDENTIALS_MANAGER = SpotifyClientCredentials(
    client_id=os.getenv("CLIENT_ID"), client_secret=os.getenv("CLIENT_SECRET")
)
SP = spotipy.Spotify(client_credentials_manager=CLIENT_CREDENTIALS_MANAGER)


def get_playlist_uri(playlist_link):
    return playlist_link.split("/")[-1].split("?")[0]


def get_simplified_track_info(track):
    artists = []
    for artist in track["track"]["album"]["artists"]:
        name = artist["name"]
        artists.append(name)

    result = {
        "name": track["track"]["name"],
        "cover": track["track"]["album"]["images"][0]["url"],
        "album": track["track"]["album"]["name"],
        "artists": ', '.join(artists)
    }
    return result


def get_tracks(PLAYLIST_LINK: str):
    print("Getting Playlist info")
    tracks = []
    playlist_uri = get_playlist_uri(PLAYLIST_LINK)

    playlist = SP.playlist_tracks(playlist_uri)
    name: str = SP.playlist(playlist_uri, fields="name")["name"]
    for track in playlist["items"]:
        result = get_simplified_track_info(track)
        tracks.append(result)

    amount = len(tracks)
    print(f'Got total {amount} tracks')

    return tracks, name


def download_track(track, path):
    name = track["name"]

    local_path = f"{path}/{name}.mp3"

    exists = os.path.exists(local_path)

    if exists:
        return

    ydl_opts = {
        "outtmpl": "{}/{}.%(ext)s".format(path, name),
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        "noplaylist": True,
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        url = ydl.extract_info(f"ytsearch:{name}", download=False, )[
            'entries'][0]["webpage_url"]
        ydl.download([url])

    print("Editing metadata.")

    audiofile = eyed3.load(local_path)
    audiofile.initTag(version=(2, 3, 0))
    audiofile.tag.artist = track["artists"]
    audiofile.tag.album = track["album"]
    audiofile.tag.title = name
    audiofile.tag.save()

    cover = track['cover']
    response = urllib.request.urlopen(cover)
    imagedata = response.read()
    audiofile.tag.images.set(3, imagedata, "image/jpeg", u"cover")

    audiofile.tag.save()


url = input("Your Playlist URL:")


tracks, name = get_tracks(url)

name = name.strip()

window = Tk()
window.iconbitmap("icon.ico")
window.withdraw()

path = filedialog.askdirectory(
    title="Select a location", initialdir="./", parent=window, mustexist=True) + "/" + name

window.destroy()

try:
    os.mkdir(path)
except OSError as err:
    err

for track in tracks:
    download_track(track, path)
    time.sleep(20)
