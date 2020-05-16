# Plex-Preroll-Builder
just a simple python script to build a recently added preroll for your plex server. piggybacking off far smarter people to automate a basic trailer builder based on the metadata of recently added movies.

# Requirements:
Python 3.6

pip

FFMPEG

PLEX-API

Pytube3


# Installation
1. donwload and install ffmpeg

https://www.ffmpeg.org/download.html

2. Install the python 3 packages
```python
sudo pip3 install pytube
sudo pip3 install ffmpeg-python
sudo pip3 install plexapi
```
3. download the project

Download and put the folder where you want the prerolls to be generated.

4. configure preroll.py to your plex server

change the below fields to the details of your plex server

```python
baseurl = 'Input Your Plex URL'
token = 'Input Your Plex Token'
plex = PlexServer(baseurl, token)
folder = "Input the directory that this is going to sit in"
```

5. run preroll.py
```
python3 preroll.py
```

it will then begin listening to your server for new files to be added. if you want to manually create some prerolls refresh the metadata on a movie and it will create the trailer for you.
