import sys
import urllib.request
import urllib.parse
import re
import os, os.path
import ffmpeg
import requests
from pytube import YouTube
from plexapi.server import PlexServer
import textwrap
import time
from dotenv import load_dotenv


# Get path to current directory
BASEDIR = os.path.abspath(os.path.dirname(__file__))
# Prepend the .env file with current directory
load_dotenv(os.path.join(BASEDIR, ".env"))

# Customise based on your server IP your servers Plex API Token and the folder you want this package to be sat in
PLEX_URL = os.environ.get("PLEX_URL")
PLEX_TOKEN = os.environ.get("PLEX_TOKEN")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
folder = os.environ.get("FOLDER")


# grabs the name of the currently refreshing movie metadata
def grab_the_name(current):
    title_place = current.find("'title':")
    title_place_end = current.find("', 'state': 5", title_place + 10)
    name = current[(title_place + 10) : title_place_end]
    print(name)
    movie_add(name)


# actively listening for state 5 (metadata complete)
def listen(msg):
    current = str(msg)
    movie_added = "'state': 5"
    if movie_added in current:
        print("Pre-rolling")
        grab_the_name(current)
    else:
        print("listening")


# go ot the library and look up the name of the movie to pull its plex id
def movie_add(name):
    section = plex.library.section("Movies")
    movie = section.get("{}".format(name))
    print(movie)

    # youtube downloading progress
    def show_progress_bar(stream, chunk, bytes_remaining):
        sys.stdout.write(f"\rdownloading...")
        sys.stdout.flush()

    # grabbing the youtube soundtrack video and converting it into an mp3 of appropriate length and adding fade out
    def buildprerollsoundtrack(music_stream, music_filelocation):
        soundtrackname = re.sub("{}".format(folder), "", music_filelocation)
        soundtracktitle = title = name.strip(".mp4")
        soundtrack = ffmpeg.input("{}".format(music_filelocation), ss=0, t=33.5)
        soundtrack = ffmpeg.filter(soundtrack, "afade", t="out", st=31.5, d=2)
        soundtrack = ffmpeg.output(soundtrack, "prerollaudio.mp3".format(title))
        ffmpeg.run(soundtrack)
        os.remove("{}".format(music_filelocation))

    # building the preroll video emptying the root folder of all downloaded contents and checking the preroll folder has the most recent 25 pre rolls
    def buildpreroll(stream, filelocation):
        title = re.sub("{}".format(folder), "", filelocation)
        title = re.sub(".mp4", "", title)
        titleoffset = ((len(title) * 33) / 2) - 7
        if titleoffset > 716:
            title = textwrap.fill(title, width=40)
            titlenl = title.find("\n")
            titleoffset = ((titlenl * 33) / 2) - 7
        description = "{}".format(summary)
        description = textwrap.fill(description, width=22)
        sidebar = ffmpeg.input("{}overlays/prerolloverlaytest.mov".format(folder))
        poster = ffmpeg.input("{}poster.jpg".format(folder))
        fadeout = ffmpeg.input("{}overlays/fadeout.mov".format(folder))
        titlefont = "{}fonts/Bebas-Regular.ttf".format(folder)
        descriptionfont = "{}fonts/cour.ttf".format(folder)
        poster = ffmpeg.filter(poster, "scale", 200, -1)
        preroll = ffmpeg.input("{}".format(filelocation), ss=10, t=33.5)
        preroll = ffmpeg.filter(preroll, "scale", 1600, -1)
        prerollaudio = ffmpeg.input("{}prerollaudio.mp3".format(folder))
        preroll = ffmpeg.overlay(sidebar, preroll, x=300, y=125)
        preroll = ffmpeg.overlay(preroll, poster, x=40, y=180, enable="gte(t,1)")
        preroll = ffmpeg.drawtext(
            preroll,
            text=title,
            fontfile=titlefont,
            x=(1106 - titleoffset),
            y=20,
            escape_text=True,
            fontcolor="0xFFFFFF@0xff",
            fontsize=76,
            enable="gte(t,1)",
        )
        preroll = ffmpeg.drawtext(
            preroll,
            text=description,
            fontfile=descriptionfont,
            x=3,
            y=500,
            escape_text=True,
            fontcolor="0xFFFFFF@0xff",
            fontsize=22,
            enable="gte(t,1)",
        )
        preroll = ffmpeg.overlay(preroll, fadeout)
        preroll = ffmpeg.output(
            prerollaudio, preroll, ("{}prerolls/{} Preroll.mp4".format(folder, title))
        )
        ffmpeg.run(preroll)
        plexsetting = plex.settings.get("cinemaTrailersPrerollID")
        plexsetting = str(plexsetting.value)
        plexsprerolllength = len(plexsetting) - 1
        plexsetting = plexsetting[2:plexsprerolllength]
        dirListing = os.listdir("{}prerolls/".format(folder))
        full_path = ["Prerolls/{0}".format(x) for x in dirListing]
        if len(dirListing) > 26:
            oldest_file = min(full_path, key=os.path.getctime)
            os.remove(oldest_file)
            plexsetting = re.sub("{}{}".format(folder, oldest_file), "", plexsetting)
        settinginput = "{}; {}prerolls/{} Preroll.mp4".format(
            plexsetting, folder, title
        )
        plex.settings.get("cinemaTrailersPrerollID").set(settinginput)
        plex.settings.save()
        print(settinginput)
        print(plex.settings.cinemaTrailersPrerollID)
        os.remove("{}poster.jpg".format(folder))
        os.remove("{}prerollaudio.mp3".format(folder))
        os.remove("{}".format(filelocation))
        print("done!")

    # grabbing the movie information such as poster and description
    summary = movie.summary
    year = movie.year
    poster_url = PLEX_URL + movie.thumb + "?X-Plex-Token=" + PLEX_TOKEN
    img_data = requests.get(poster_url).content
    with open("poster.jpg".format(name), "wb") as handler:
        handler.write(img_data)

    print(summary)
    print(year)

    # looking up the top movie theatricle trailer with some extra stipulations to avoid playlist videos etc
    query_string = urllib.parse.urlencode(
        {"search_query": name + " Theatrical Trailer {}".format(year)}
    )
    html_content = urllib.request.urlopen(
        "http://www.youtube.com/results?" + query_string + "&sp=EgIgAQ%253D%253D"
    )
    search_results = re.findall(
        r"href=\"\/watch\?v=(.{11})", html_content.read().decode()
    )
    url = "http://www.youtube.com/watch?v=" + search_results[0]
    # looking up the top soundtrack youtube video
    music_query_string = urllib.parse.urlencode({"search_query": name + "soundtrack"})
    music_html_content = urllib.request.urlopen(
        "http://www.youtube.com/results?" + music_query_string + "&sp=EgIQAQ%253D%253D"
    )
    music_search_results = re.findall(
        r"href=\"\/watch\?v=(.{11})", music_html_content.read().decode()
    )
    music_url = "http://www.youtube.com/watch?v=" + music_search_results[0]

    print(url)
    print(music_url)
    # downloading the soundtrack for the movie from the top result found in the search
    yt = YouTube(url)
    music_yt = YouTube(music_url)
    music_yt.register_on_progress_callback(show_progress_bar)
    music_yt.register_on_complete_callback(buildprerollsoundtrack)
    music_yt.streams.get_highest_resolution().download(
        output_path=("{}".format(folder)), filename="{} soundtrack".format(name)
    )

    # downloading the movie theatricle trailer from the top result foind in the search
    yt.register_on_progress_callback(show_progress_bar)
    yt.register_on_complete_callback(buildpreroll)
    yt.streams.get_highest_resolution().download(
        output_path=("{}".format(folder)), filename="{}".format(name)
    )


# good old listen loop
if __name__ == "__main__":
    try:
        plex = PlexServer(PLEX_URL, PLEX_TOKEN)
        listener = plex.startAlertListener(listen)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()
