# Plex-Preroll-Builder
just a simple python script to build a recently added preroll for your plex server. piggybacking off far smarter people to automate a basic trailer builder based on the metadata of recently added movies.

# Requirements:
Python 3.6

pip

FFMPEG

PLEX-API

Pytube3

python-dotenv

flask



# Installation
1. Set up your plex to speak to prerolls
On the plex admin panel go to settings:
```
general -> turn on push notifications
webhooks -> Serverip/plexpreroll
```
2. Install ffmpeg
``` ( ubuntu / debian based )
sudo apt-get install ffmpeg -y
``` 

https://www.ffmpeg.org/download.html

3. Install the python 4 packages 

( server headless )
```python
sudo pip3 install \
          opencv-contrib-python-headless \
          pgit+https://github.com/pytube/pytube
          ffmpeg-python \
          plexapi \
          python-dotenv \
          flask \
```
( standard desktop environments ) 
```python
sudo pip3 install \
          opencv-python
          git+https://github.com/pytube/pytube
          ffmpeg-python \
          plexapi \
          python-dotenv \
          flask \

```

4. download the project

Download and put the folder where you want the prerolls to be generated.

5. configure preroll.py to your plex server

change the below fields to the details of your plex server

```python
baseurl = 'Input Your Plex URL'
token = 'Input Your Plex Token'
folder = "Input the directory that this is going to sit in"
```

6. run preroll.py
```
python3 preroll.py
```

it will then begin listening to your server for new files to be added.
