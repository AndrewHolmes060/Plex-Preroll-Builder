import sys
import urllib.request
import urllib.parse
import re
import os, os.path
import ffmpeg
import requests
import json
import textwrap
import time
import pytube
from pytube import YouTube
from plexapi.server import PlexServer
from dotenv import load_dotenv
from flask import Flask, request, Response

app = Flask(__name__)

# Get path to current directory
BASEDIR = os.path.abspath(os.path.dirname(__file__))
# Prepend the .env file with current directory
load_dotenv(os.path.join(BASEDIR, ".env"))

# Customise based on your server IP your servers Plex API Token and the folder you want this package to be sat in
PLEX_URL = os.environ.get("PLEX_URL")
PLEX_TOKEN = os.environ.get("PLEX_TOKEN")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
folder = os.environ.get("FOLDER")

# youtube downloading progress
def show_progress_bar(stream, chunk, bytes_remaining):
    sys.stdout.write(f"\rdownloading...")
    sys.stdout.flush()

# grabbing the youtube soundtrack video and converting it into an mp3 of appropriate length and adding fade out
def buildprerollsoundtrack(music_stream, music_filelocation):
    soundtrack = ffmpeg.input("{}".format(music_filelocation), ss=0, t=33.5)
    soundtrack = ffmpeg.filter(soundtrack, "afade", t="out", st=31.5, d=2)
    soundtrack = ffmpeg.output(soundtrack, "{}prerollaudio.mp3".format(folder))
    ffmpeg.run(soundtrack)
    os.remove("{}".format(music_filelocation))

# building the preroll video emptying the root folder of all downloaded contents and checking the preroll folder has the most recent 25 pre rolls
def buildpreroll(stream, filelocation):
    titleoffset = ((len(name) * 33) / 2) - 7
    if titleoffset > 716:
        title = textwrap.fill(name, width=40, break_long_words=False)
        titlenl = title.find("\n")
        titleoffset = ((titlenl * 33) / 2) - 7
    description = textwrap.fill(summary, width=22, break_long_words=False)
    num_of_lines = description.count("\n")
    if num_of_lines > 22:
        descriptionSize = 580 / num_of_lines
    else:
       descriptionSize = 26 
    sidebar = ffmpeg.input("{}overlays/prerolloverlaytest.mov".format(folder))
    poster = ffmpeg.input("{}poster.jpg".format(folder))
    fadeout = ffmpeg.input("{}overlays/fadeout.mov".format(folder))
    titlefont = "{}fonts/Bebas-Regular.ttf".format(folder)
    descriptionfont = "{}fonts/Roboto-Light.ttf".format(folder)
    poster = ffmpeg.filter(poster, "scale", 200, -1)
    preroll = ffmpeg.input("{}".format(filelocation), ss=10, t=33.5)
    preroll = ffmpeg.filter(preroll, "scale", 1600, -1)
    prerollaudio = ffmpeg.input("{}prerollaudio.mp3".format(folder))
    preroll = ffmpeg.overlay(sidebar, preroll, x=300, y=125)
    preroll = ffmpeg.overlay(preroll, poster, x=40, y=190, enable="gte(t,1)")
    if CriticRating == "":
        preroll = ffmpeg.drawtext(
            preroll,
            text="Audiance Rating: {}%".format(AudienceRating),
            fontfile=titlefont,
            x=3,
            y=145,
            escape_text=True,
            fontcolor="0xFFFFFF@0xff",
            fontsize=36,
            enable="gte(t,1)",
        )
    else:
        preroll = ffmpeg.drawtext(
            preroll,
            text="Audiance Rating: {}%".format(AudienceRating),
            fontfile=titlefont,
            x=3,
            y=165,
            escape_text=True,
            fontcolor="0xFFFFFF@0xff",
            fontsize=32,
            enable="gte(t,1)",
        )

        preroll = ffmpeg.drawtext(
            preroll,
            text="Critic Rating: {}%".format(CriticRating),
            fontfile=titlefont,
            x=3,
            y=135,
            escape_text=True,
            fontcolor="0xFFFFFF@0xff",
            fontsize=32,
            enable="gte(t,1)",
        )
    preroll = ffmpeg.drawtext(
        preroll,
        text=name,
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
        fontsize=descriptionSize,
        enable="gte(t,1)",
    )
    preroll = ffmpeg.overlay(preroll, fadeout)
    preroll = ffmpeg.output(
        prerollaudio, preroll, ("{}prerolls/{} Preroll.mp4".format(folder, name))
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
        plexsetting, folder, name
    )
    plex.settings.get("cinemaTrailersPrerollID").set(settinginput)
    plex.settings.save()
    os.remove("{}poster.jpg".format(folder))
    os.remove("{}prerollaudio.mp3".format(folder))
    os.remove("{}".format(filelocation))
    print("done!")

@app.route('/plexpreoll', methods=['POST'])
def listener():
    data = request.form
    response = Response(status=200)
    # need to set JSON like {'username': 'febin'}
    try:
        webhook = json.loads(data['payload'])
    except:
	    print("No payload found")
    
    event = webhook['event']
    print("Event: " + event)
    if event == 'library.new':
            metadata = webhook['Metadata']
            isitamovie = metadata['type']
            if isitamovie == 'movie':
                global name
                name = metadata['title']
                global summary
                summary = metadata['summary']
                global year
                year = metadata['year']
                global movieThumb
                movieThumb = metadata['thumb']
                global AudienceRating
                AudienceRating = int(metadata['audienceRating'] * 10)
                global CriticRating
                try:
                    CriticRating = int(metadata['rating'] * 10)
                except:
                    CriticRating = ""
                    print(name)
                    

                # grabbing the movie information such as poster and description
                
                poster_url = PLEX_URL + movieThumb + "?X-Plex-Token=" + PLEX_TOKEN
                img_data = requests.get(poster_url).content
                with open("poster.jpg", "wb") as handler:
                    handler.write(img_data)

                # looking up the top movie theatrical trailer with some extra stipulations to avoid playlist videos etc
                search_query = ("{} Official Theatrical Trailer {}".format(name, year))
                search_query = search_query.replace(" ", "+")
                html = urllib.request.urlopen("https://www.youtube.com/results?search_query={}&sp=EgQYASAB".format(search_query))
                search_results = re.findall(r"watch\?v=(\S{11})", html.read().decode())

                # looking up the top soundtrack youtube video
                music_search_query = ("{} {} soundtrack".format(name, year))
                music_search_query = music_search_query.replace(" ", "+")
                music_html = urllib.request.urlopen("https://www.youtube.com/results?search_query={}&sp=EgIYAQ%253D%253D".format(music_search_query))
                music_search_results = re.findall(r"watch\?v=(\S{11})", music_html.read().decode())
                # downloading the soundtrack for the movie from the top available result found in the search and second one if the first is unavailable 
                for i in music_search_results:
                    try:
                        music_url = "http://www.youtube.com/watch?v=" + i
                        music_yt = YouTube(music_url)
                        print("Downloading soundtrack video: {}".format(music_url))
                        music_yt.register_on_progress_callback(show_progress_bar)
                        music_yt.register_on_complete_callback(buildprerollsoundtrack)
                    except pytube.exceptions.VideoUnavailable as e:
                        print("Video is unavaialable due to {}, skipping.".format(e))
                        continue
                    else:
                        music_yt.streams.get_highest_resolution().download(
                            output_path=("{}".format(folder)), filename="{}".format(name))
                        break
                # downloading the top theatrical trailer for the movie from the top available result found in the search and second one if the first is unavailable 
                for v in search_results:
                    try:
                        url = "http://www.youtube.com/watch?v=" + v
                        yt = YouTube(url)
                        print("Downloading Theatrical Trailer: {}".format(url))
                        yt.register_on_progress_callback(show_progress_bar)
                        yt.register_on_complete_callback(buildpreroll)
                    except pytube.exceptions.VideoUnavailable as e:
                        print("Video is unavaialable due to {}, skipping.".format(e))
                        continue
                    else:
                        yt.streams.get_highest_resolution().download(
                            output_path=("{}".format(folder)), filename="{}".format(name))
                        break
    return response

if __name__ == '__main__':
    app.run()





