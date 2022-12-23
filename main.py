from __future__ import unicode_literals
from unicodedata import name
from spotipy.oauth2 import SpotifyClientCredentials
from tkinter import Tk, filedialog
from dotenv import load_dotenv
from colorama import init, Fore as color
import urllib
import yt_dlp
import spotipy
import eyed3
import time
import json
import os

init()

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
        "artists": ", ".join(artists),
    }
    return result


def get_tracks(PLAYLIST_LINK: str):
    print("Getting Playlist info")
    tracks = []
    playlist_uri = get_playlist_uri(PLAYLIST_LINK)

    try:
        with open(f"cache/playlist/{playlist_uri}.json", "rb") as f:
            tracks, playlist = json.loads(f.read())
            print("cached playlist")
    except:
        playlist = SP.playlist_tracks(playlist_uri)
        name: str = SP.playlist(playlist_uri, fields="name")["name"]
        for track in playlist["items"]:
            result = get_simplified_track_info(track)
            tracks.append(result)

        with open(f"cache/playlist/{playlist_uri}.json", "w", encoding="utf8") as f:
            f.write(json.dumps([track, name], indent=4))

    amount = len(tracks)
    print(f"Got total {amount} tracks")

    return tracks, name


def download_track(track, path):
    name = track["name"]

    local_path = f"{path}/{name}.mp3"

    exists = os.path.exists(local_path)

    if exists:
        return print("Already exists.")

    ydl_opts = {
        "outtmpl": "{}/{}.%(ext)s".format(path, name),
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }
        ],
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        url = ydl.extract_info(f"ytsearch:{name} lyrics", download=False,)["entries"][
            0
        ]["webpage_url"]
        ydl.download([url])

    print("Editing metadata.")

    audiofile = eyed3.load(local_path)
    audiofile.initTag(version=(2, 3, 0))
    audiofile.tag.artist = track["artists"]
    audiofile.tag.album = track["album"]
    audiofile.tag.title = name
    audiofile.tag.save()

    cover = track["cover"]
    try:
        file_name = os.path.split(cover)[1]
        with open(f"cache/cover/{file_name}", "rb") as f:
            image_data = f.read()
        print("cached cover")
    except:
        image_data = urllib.request.urlopen(cover).read()
        file_name = os.path.split(cover)[1]
        with open(f"cache/cover/{file_name}", "wb") as f:
            f.write(image_data)
    audiofile.tag.images.set(3, image_data, "image/jpeg", "cover")

    audiofile.tag.save()
    time.sleep(20)


mkdir = lambda n: (not os.path.exists(n)) and os.mkdir(n)


url = input("Your Playlist URL:")

tracks, name = get_tracks(url)

name = name.strip()

window = Tk()
window.iconbitmap("icon.ico")
window.withdraw()

path = (
    filedialog.askdirectory(
        title="Select a location", initialdir="./", parent=window, mustexist=True
    )
    + "/"
    + name
)

window.destroy()

mkdir(path)
mkdir("cache")
mkdir("cache/cover")
mkdir("cache/playlist")

for i, track in enumerate(tracks):
    title = track["name"]
    print(f"\n\n{color.GREEN} { 1 + i }. { title } {color.RESET}\n")
    download_track(track, path)
