import math

import PIL
import requests
import random
import discord
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import imageio
import io
import numpy as np
import re

import urllib.parse
from commands.connect import find_user


headers = {'Accept': 'application/json'}

VALID_PERIODS = {"7day", "1month", "3month", "6month", "12month", "overall"}

def resolve_lastfm_user(message, args) -> str | None:
    if len(args) > 0 and args[0] not in VALID_PERIODS:
        return args[0]
    user = find_user(message.author.id)
    if user is not None:
        return user.strip()
    return None

def resolve_period(args) -> str:
    for arg in args:
        if arg in VALID_PERIODS:
            return arg
    return "12month"

async def topster(message, lastfmKey):
    args = message.content.split(" ")[1:]

    if len(args) > 0 and args[0] in ("-orbit", "-pvc"):
        await orbit_topster(message, lastfmKey, pvc=(args[0] == "-pvc"))
        return

    user = resolve_lastfm_user(message, args)
    if not user:
        await message.channel.send("Please specify a lastfm username or link your account with !auxconnect.")
        return

    period = resolve_period(args)
    working = await message.channel.send("Working on it! (this might take a while)")

    try:
        limit = 12
        total_limit = limit * limit

        r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user + '&limit=' + str(total_limit) + '&page=1&period=' + period +'&api_key=' + lastfmKey + '&format=json', headers=headers)
        rawjson = r.json()

        if 'topalbums' not in rawjson or 'album' not in rawjson['topalbums']:
            await message.channel.send(f"Error: couldn't fetch albums for user `{user}`.")
            await working.delete()
            return

        topalbums = rawjson['topalbums']['album']
    except Exception as e:
        await message.channel.send(f"Error fetching albums: {e}")
        await working.delete()
        return

    try:
        album_size = 170
        vert_offset = 32
        hor_offset = 32
        pad = 100

        # download all album covers once
        album_images = []
        for i in range(len(topalbums)):
            album = topalbums[i]
            if album is None or 'image' not in album or album['image'][2]['#text'] == "":
                continue

            init_im = requests.get(album['image'][2]['#text'])
            bytes_im = io.BytesIO(init_im.content)
            try:
                cv_im = Image.open(bytes_im)
            except PIL.UnidentifiedImageError:
                continue
            cv_im = cv_im.convert("RGBA")

            scale = 0.8 * (1 - (i / max(total_limit - 1, 1))) + 0.6
            cv_im = cv_im.resize((int(cv_im.size[0] * scale), int(cv_im.size[1] * scale)))
            album_images.append(cv_im)

        # create collage, retry with increasing spacing
        max_attempts = 5
        skipped_albums = 0
        for attempt_num in range(max_attempts):
            vert_offset += 3
            hor_offset += 3

            h = (album_size + vert_offset) * limit + 2 * pad
            w = (album_size + hor_offset) * limit + 2 * pad
            image = np.zeros((h, w, 4), dtype=np.uint8)

            skipped_albums = 0

            for cv_im in album_images:
                rotate_angle = random.randint(-5, 5)
                cv_im_r = cv_im.rotate(rotate_angle, expand=True)

                np_im = np.array(cv_im_r)
                size = np_im.shape[0]

                mask = np_im[:, :, 3] != 0
                img_mask = np_im[mask]

                placed = False
                for attempt in range(100):
                    x = random.randint(pad, image.shape[0] - pad - size)
                    y = random.randint(pad, image.shape[1] - pad - size)

                    region = image[x:x+size, y:y+size][mask]
                    overlap = np.count_nonzero(region[:, 3] > 0)
                    if overlap > 3500:
                        continue

                    image[x:x+size, y:y+size][mask] = img_mask
                    placed = True
                    break

                if not placed:
                    skipped_albums += 1
                    break

            if skipped_albums == 0:
                break
        else:
            await message.channel.send(f"Couldn't place all albums after {max_attempts} attempts, sending best result.")

        # lay background image
        back_small = Image.open(f"assets/topster_bg.jpeg")
        back_small = back_small.convert("RGBA")
        back_small = back_small.resize((image.shape[1], image.shape[0]), Image.Resampling.LANCZOS)
        canvas = np.array(back_small)

        mask = image[:, :, 3] > 125
        canvas[0:image.shape[0], 0:image.shape[1]][mask] = image[mask]

        im = Image.fromarray(canvas)
        im.save("chart.png")

        await message.channel.send(file=discord.File('chart.png'))
        await message.channel.send(f"Skipped {skipped_albums}/{total_limit} albums")
    except Exception as e:
        await message.channel.send(f"Error generating topster: {e}")
    finally:
        await working.delete()

async def orbit_topster(message, lastfmKey, pvc=False):
    args = message.content.split(" ")[1:]  # includes "-orbit"/"-pvc"
    remaining = args[1:]  # after the flag
    user = resolve_lastfm_user(message, remaining)
    if not user:
        await message.channel.send("Please specify a lastfm username or link your account with !auxconnect.")
        return

    period = resolve_period(remaining)

    working = await message.channel.send("Working on it!")

    try:
        ring_lengths = [0, 8, 16, 20, 27, 30]
        rings = len(ring_lengths)
        total_limit = sum(ring_lengths)
        limit = int(math.sqrt(total_limit))

        album_size = 174
        vert_offset = 32
        hor_offset = 32

        pad = 300

        scaling_factor = 1/2
        album_size = int(int(int(album_size * scaling_factor) / 2) * 2)  # need to make sure value is even
        vert_offset = int(vert_offset * scaling_factor)
        hor_offset = int(hor_offset * scaling_factor)
        pad = int(pad * scaling_factor)

        # h = int((album_size + vert_offset) * limit + 2 * pad)
        # w = int((album_size + hor_offset) * limit + 2 * pad)
        h = int((ring_lengths[-1] * album_size) / 2)
        w = int((ring_lengths[-1] * album_size) / 2)
        canvas_size = h

        bg_path = "assets/pvc_bg.png" if pvc else "assets/topster_bg.jpeg"
        back_small = Image.open(bg_path)
        back_small = back_small.convert("RGBA")
        back_small = back_small.resize((h, w), Image.Resampling.LANCZOS)
        canvas = np.array(back_small)

        top_text = None
        top_text_frames = 0
        if pvc:
            top_text = Image.open(f"assets/pvc_text_20fps.gif")
            top_text_frames = top_text.n_frames

        images = [None] * total_limit

        r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user + '&limit=' + str(total_limit * 2) + '&page=1&period=' + period + '&api_key=' + lastfmKey + '&format=json', headers=headers)
        rawjson = r.json()

        if 'topalbums' not in rawjson or 'album' not in rawjson['topalbums']:
            await message.channel.send(f"Error: couldn't fetch albums for user `{user}`.")
            await working.delete()
            return

        topalbums = rawjson['topalbums']['album']

        albums_saved = 0
        i = 0
        albumnames = []
        while albums_saved < total_limit and i < len(topalbums):
            album = topalbums[i]
            name = album['name']

            if len(album['image'][2]['#text']) == 0:
                i += 1
                continue

            init_im = requests.get(album['image'][2]['#text'])
            bytes_im = io.BytesIO(init_im.content)
            try:
                cv_im = Image.open(bytes_im)
            except PIL.UnidentifiedImageError:
                i += 1
                continue
            cv_im = cv_im.convert("RGBA")
            cv_im = cv_im.resize((album_size, album_size), Image.Resampling.LANCZOS)
            if name not in albumnames:
                images[albums_saved] = cv_im
                albums_saved += 1

            albumnames.append(name)
            i += 1

        framerate = 20
        frames = []
        theta_offset = 0
        duration = 5

        for frame in range(framerate * duration):
            f_canvas = canvas.copy()
            positions = []
            for ring in range(rings):
                radius = ring * album_size + 40
                positions.append([])
                num_albums = ring_lengths[ring]
                ring_theta_offset = -theta_offset
                for album in range(num_albums):
                    position = (int(canvas_size/2) + radius * math.cos(album / num_albums * 2 * math.pi + ring_theta_offset),
                                int(canvas_size/2) + radius * math.sin(album / num_albums * 2 * math.pi + ring_theta_offset))
                    positions[ring].append(position)

            album_index = 0
            for ring in positions:
                for pos in ring:
                    cv_im = images[album_index]
                    f_canvas[int(pos[0]) - int(album_size/2):int(pos[0]) + int(album_size/2), int(pos[1]) - int(album_size/2):int(pos[1]) + int(album_size/2)] = np.array(cv_im)
                    album_index += 1

            theta_offset = (frame / (framerate * duration)) * 2 * math.pi

            if pvc and top_text is not None:
                closest_index = int((frame / (framerate * duration)) * top_text_frames)
                top_text.seek(closest_index)
                top_text_frame = top_text.convert("RGBA")
                top_text_frame = top_text_frame.resize((canvas_size, canvas_size), Image.Resampling.LANCZOS)
                top_text_frame_mask = np.array(top_text_frame)[:, :, 3] != 0
                f_canvas[0:canvas_size, 0:canvas_size][top_text_frame_mask] = np.array(top_text_frame)[top_text_frame_mask]

            f_canvas = Image.fromarray(f_canvas)
            f_canvas = f_canvas.resize((512, 512), Image.Resampling.LANCZOS)
            f_canvas = np.array(f_canvas)

            frames.append(f_canvas)

        imageio.mimsave('chart.gif', frames, loop=0, duration=0.5, fps=framerate)
        try:
            await message.channel.send(file=discord.File('chart.gif'))
        except discord.HTTPException as e:
            if e.status == 413:
                # compress and retry with smaller resolution
                smaller_frames = [np.array(Image.fromarray(f).resize((384, 384), Image.Resampling.LANCZOS)) for f in frames]
                imageio.mimsave('chart.gif', smaller_frames, loop=0, duration=0.5, fps=framerate)
                await message.channel.send(file=discord.File('chart.gif'))
            else:
                raise
    except Exception as e:
        await message.channel.send(f"Error generating orbit topster: {e}")
    finally:
        await working.delete()

async def playster(message, spotifyKey, lastfmKey):
    args = message.content.split(" ")[1:]

    topalbums = []
    #[topalbums.extend(albums_from_playlist(playlist, spotifyKey)) for playlist in args]
    if len(args) == 0:
        topalbums.extend(albums_from_user(message, spotifyKey))
    else:
        topalbums.extend(albums_from_playlist(args[0], spotifyKey))

    args = [int(x) for x in args[1:]]

    albumcovers = []
    albumnames = []
    albumartists = []

    #topalbums.sort(key=lambda x: x['album']['popularity'], reverse=True)

    #topalbums.sort(key=lambda x: x['album']['release_date'], reverse=False)

    for album in topalbums:
        # if album['album']['release_date'][:4] != '2024':
        #     continue

        #await message.channel.send(content=album['album']['tracks']['items'][0]['uri'])
        #r = requests.post('https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks', headers=headers, json=body)
        #r = requests.get('https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks?limit=100&fields=' + fields, headers=headers)

        if 'track' in album:
            album = album['track']
        name = album['album']['name']
        artist = album['album']['artists'][0]['name']
        #print(name)

        if len(album['album']['images']) == 0:
            await message.channel.send("Skipped album " + name)
            continue

        # r = requests.get('http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=' + lastfmKey + '&artist='
        #                  + urllib.parse.quote(artist) + '&album=' + urllib.parse.quote(name) +
        #                  '&user=' + user + '&format=json', headers=headers)
        # fmjson = r.json()
        # print(fmjson['album'])
        # print(fmjson['album']['artist'])
        # print(fmjson['album']['name'])
        # print(list(fmjson['album'].keys())[-1])
        # print(fmjson['album'][list(fmjson['album'].keys())[-1]])
        #
        # if 'tracks' not in fmjson['album'] or 'track' not in fmjson['album']['tracks']:
        #     continue
        #
        # if 'album' not in fmjson:
        #     await message.channel.send("Not found on lastfm " + name)
        #     continue
        # if 'userplaycount' not in fmjson['album']:
        #     await message.channel.send("Not found playcount lastfm " + name)
        #     continue
        #
        # albumplays = fmjson['album']['userplaycount']
        # listened = True
        #
        # if albumplays == 0:
        #     #await message.channel.send("Skipped album (0 total plays) " + name)
        #     listened = False
        #     continue
        #
        # #await message.channel.send(name + " Spotify tracks:")
        # for track in album['album']['tracks']['items']:
        #     #await message.channel.send(track['name'])
        #     name = track['name']
        #
        #     r = requests.get('http://ws.audioscrobbler.com/2.0/?method=track.getinfo&api_key=' + lastfmKey + '&artist='
        #                      + urllib.parse.quote(artist) + '&track=' + urllib.parse.quote(name) +
        #                      '&user=' + user + '&format=json', headers=headers)
        #     trackjson = r.json()
        #
        #     #print(trackjson)
        #
        #     if 'error' in trackjson:
        #         await message.channel.send("Not found on lastfm " + name)
        #         continue
        #
        #     if str(trackjson['track']['userplaycount']) == '0':
        #         #await message.channel.send("Skipped track (0 total plays) " + name)
        #         listened = False
        #         break
        #
        #     #await message.channel.send(track['name'] + " - " + str(trackjson['track']['userplaycount']) + " " + str(trackjson['track']['name']))
        #
        # #return

        init_im = requests.get(album['album']['images'][1]['url'])
        bytes_im = io.BytesIO(init_im.content)
        cv_im = Image.open(bytes_im)
        cv_im = cv_im.convert("RGBA")
        cv_im = cv_im.resize((300, 300), Image.Resampling.LANCZOS)

        # if not listened:
        #     converter = PIL.ImageEnhance.Color(cv_im)
        #     cv_im = converter.enhance(0.0)
        # else:
        #     bg = np.zeros((300, 300, 4), dtype=np.uint8)
        #     bg[:, :, 3] = 255
        #     bg[:, :, 2] = 255
        #     bg[:, :, 0] = 255
        #     cv_im = cv_im.resize((250, 250), Image.Resampling.LANCZOS)
        #     cv_im = np.array(cv_im)
        #     bg[25:275, 25:275] = cv_im
        #     cv_im = Image.fromarray(bg)


        if name not in albumnames:
            albumcovers.append(cv_im)

            #await message.channel.send(name)
            #await message.channel.send(album['track']['album']['images'][1]['url'])

            albumnames.append(name)
            albumartists.append(artist)

    for arg in args:
        blank_album = np.zeros((300, 300, 4), dtype=np.uint8)
        blank_album = Image.fromarray(blank_album)
        albumcovers.insert(arg, blank_album)
        albumnames.insert(arg, "BLANK")
        albumartists.insert(arg, "BLANK")

    # find best chart size
    size = math.ceil(math.sqrt(len(albumcovers)))
    # size = 9
    blank_albums = size*size - len(albumcovers)

    image = []
    rows = []

    for i in range(len(albumcovers)):
        album = albumcovers[i]

        album_pad = np.zeros((320, 320, 4), dtype=np.uint8)
        album_pad[10:310, 10:310] = np.array(album)
        album = Image.fromarray(album_pad)

        rows.append(album)

        if len(rows) % size == 0:
            image.append(np.hstack(rows))
            rows = []

    if len(rows) % size != 0:
        blank_albums = size - (len(rows) % size)
        for i in range(blank_albums):
            blank_album = np.zeros((320, 320, 4), dtype=np.uint8)
            blank_album = Image.fromarray(blank_album)
            rows.append(blank_album)

        image.append(np.hstack(rows))
        rows = []
    elif len(rows) != 0:
        image.append(np.hstack(rows))

    image = np.vstack(image)
    Image.fromarray(image).save("chart.png")

    text_img = np.zeros((image.shape[0], image.shape[1], 4), dtype=np.uint8)

    #image = np.concatenate(image, axis=1)
    text_img = Image.fromarray(text_img)
    artist_albums = [albumartists[i] + " - " + albumnames[i] for i in range(len(albumnames))]
    name_draw = ImageDraw.Draw(text_img)
    for i in range((len(albumnames)//size) + 1):
        offset = 10 + 320*i

        send_message = "\n".join(artist_albums[i*size:(i+1)*size]) + "\n"
        name_draw.text((10, offset), send_message, font=ImageFont.truetype("assets/Andale Mono.ttf", 30), fill=(255,255,255))

        #await message.channel.send(content=send_message)

    text_img.save("text.png")


    try:
        await message.channel.send(file=discord.File('chart.png'))
    except discord.HTTPException as e:
        if e.status == 413:
            await message.channel.send("Playlist is too big to send as a chart! Trying jpeg. (pinging <@!404832801742127122>)")
            Image.fromarray(image).convert("RGB").save("chart.jpg", quality=85)
            await message.channel.send(file=discord.File('chart.jpg'))
        else:
            raise
    try:
        await message.channel.send(file=discord.File('text.png'))
    except discord.HTTPException as e:
        if e.status == 413:
            text_img.convert("RGB").save("text.jpg", quality=85)
            await message.channel.send(file=discord.File('text.jpg'))
        else:
            raise

def albums_from_playlist(playlist: str, spotifyKey: str) -> list:
    topalbums = []

    playlist_id = re.search("(?!$)[a-zA-Z0-9]{10,}", playlist).group(0)

    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + spotifyKey}
    fields = "total"
    #fields = "items.track.album(name, images, artists, preview_url)"
    r = requests.get('https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks?limit=100&fields=' + fields, headers=headers)
    rawjson = r.json()

    total = rawjson['total']
    iterations = math.ceil(total / 100)  # for max_limit of 100

    #fields = "items.track.album(name, images, artists, preview_url)"
    fields = "items.track.album(name, images, artists)"

    for i in range(iterations):
        r = requests.get('https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks?limit=100&offset=' + str(i*100) + '&fields=' + fields, headers=headers)
        rawjson = r.json()
        topalbums.extend(rawjson['items'])

    return topalbums

def albums_from_user(message, spotifyKey: str) -> list:
    topalbums = []

    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + spotifyKey}
    r = requests.get('https://api.spotify.com/v1/me/albums', headers=headers)
    rawjson = r.json()

    total = rawjson['total']
    iterations = math.ceil(total / 50)  # for max_limit of 100

    for i in range(iterations):
        r = requests.get('https://api.spotify.com/v1/me/albums?limit=50&offset=' + str(i*50), headers=headers)
        rawjson = r.json()
        topalbums.extend(rawjson['items'])
    #
    # for album in topalbums:
    #     name = album['album']['name']
    #     artist = ", ".join([artist['name'] for artist in album['album']['artists']])
    #     #await message.channel.send(artist + " - " + name)

    return topalbums
