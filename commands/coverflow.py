import io
import imageio
from PIL import Image, ImageDraw, ImageFont

import discord
import imageio
import requests
from scipy.ndimage import rotate
import numpy as np
import cv2
import math
from commands.connect import find_user

headers = {'Accept': 'application/json'}

"""
Creates an animated coverflow visualization from a user's top last.fm albums.

Generates a 3D coverflow effect with album covers that transition smoothly
using perspective transforms and bezier easing.

Args:
    message: Discord message, optionally containing a last.fm username and period
    lastfmKey: Last.fm API key

Sends:
    GIF file to the Discord channel showing the animated coverflow
"""
async def coverflow(message: discord.Message, lastfmKey: str):
    args = message.content.split(" ")[1:]

    user = args[0] if len(args) > 0 else None
    if not user:
        linked = find_user(message.author.id)
        if linked:
            user = linked.strip()
        else:
            await message.channel.send("Please specify a lastfm username or link your account with !connect.")
            return

    period = args[1] if len(args) > 1 else "12month"
    limit = 15

    S = 500  # canvas size
    cover_size = 150
    half = cover_size // 2
    center = S // 2

    covers = []
    names = []
    artists = []

    r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user + '&limit=' + str(limit) + '&period=' + period + '&api_key=' + lastfmKey + '&format=json', headers=headers)
    rawjson = r.json()
    albums = rawjson['topalbums']['album']

    blank = np.zeros((S, S, 4), dtype=np.uint8)
    for album in albums:
        name = album['name']
        artist = album['artist']['name']
        print(name)

        if len(album['image'][2]['#text']) == 0:
            continue

        init_im = requests.get(album['image'][2]['#text'])
        bytes_im = io.BytesIO(init_im.content)
        try:
            cv_im = Image.open(bytes_im)
        except Exception:
            continue
        cv_im = cv_im.convert("RGBA")

        names.append(name)
        artists.append(artist)
        cv_im = cv_im.resize((cover_size, cover_size), Image.Resampling.LANCZOS)
        frame = blank.copy()
        frame[center-half:center+half, center-half:center+half] = np.array(cv_im)
        covers.append(frame)

    canvas = np.zeros((S, S, 4), dtype=np.uint8)
    canvas[:, :, 3] = 255

    frames = []
    durations = []

    identity_matrix = np.array([[1, 0, 0],
                                [0, 1, 0],
                                [0, 0, 1]], dtype=np.float32)

    c1, c2 = center - half, center + half
    pts1 = np.float32([[c1, c1], [c2, c1], [c1, c2], [c2, c2]])
    pts2_start = np.float32([[S-148, 208], [S-82, 160], [S-148, 293], [S-82, 340]])
    M_start = cv2.getPerspectiveTransform(pts1, pts2_start)
    M = cv2.getPerspectiveTransform(pts1, pts2_start)

    for cover in range(len(covers)):
        prev_cover = covers[cover - 1] if cover > 0 else covers[-1]
        prev_cover = np.flip(prev_cover, axis=1)
        current_cover = covers[cover]
        current_cover = np.flip(current_cover, axis=1)
        next_cover = covers[(cover + 1) % len(covers)]
        next_next_cover = covers[(cover + 2) % len(covers)]

        transform_frames = 15
        for i in range(transform_frames):
            percent_transform = bezier(i / (1.0 * transform_frames))
            percent_transform_r = tempered_bezier(i / (1.0 * transform_frames))

            frame_M = percent_transform_r * M + (1 - percent_transform_r) * identity_matrix
            frame_M_start = percent_transform * identity_matrix + (1 - percent_transform) * M_start

            red_square_t = cv2.warpPerspective(current_cover, frame_M, (S, S))
            red_square_t = np.flip(red_square_t, axis=1)
            blue_square_t = cv2.warpPerspective(next_cover, frame_M_start, (S, S))

            next_red_square = cv2.warpPerspective(next_next_cover, M_start, (S, S))
            next_red_square = next_red_square * percent_transform_r

            prev_blue_square = cv2.warpPerspective(prev_cover, M_start, (S, S))
            prev_blue_square = np.flip(prev_blue_square, axis=1)

            canvas_t = canvas.copy()
            for layer in [prev_blue_square, red_square_t, next_red_square, blue_square_t]:
                m = layer[:, :, 3] != 0
                canvas_t[m] = layer[m]

            canvas_t = canvas_t[125:400, 75:425]
            frames.append(canvas_t)
            durations.append(50)

        red_square_t = cv2.warpPerspective(current_cover, M, (S, S))
        red_square_t = np.flip(red_square_t, axis=1)
        blue_square_t = cv2.warpPerspective(next_cover, identity_matrix, (S, S))
        next_red_square = cv2.warpPerspective(next_next_cover, M, (S, S))

        canvas_final = canvas.copy()
        for layer, m in [(red_square_t, red_square_t[:, :, 3] != 0),
                         (blue_square_t, blue_square_t[:, :, 3] != 0),
                         (next_red_square, next_red_square[:, :, 3] != 0)]:
            canvas_final[m] = layer[m]

        canvas_final = Image.fromarray(canvas_final)
        still_text = ImageDraw.Draw(canvas_final)
        text_cover = cover + 1 if cover < len(covers) - 1 else 0
        still_text.text((S//2, 360), names[text_cover], font=ImageFont.truetype("assets/Andale Mono.ttf", 15), fill=(255,255,255), anchor="mm")
        still_text.text((S//2, 380), artists[text_cover], font=ImageFont.truetype("assets/Andale Mono.ttf", 15), fill=(255,255,255), anchor="mm")
        canvas_final = np.array(canvas_final)
        canvas_final = canvas_final[125:400, 75:425]

        frames.append(canvas_final)
        durations.append(1500)

    imageio.mimsave('chart.gif', frames, loop=0, duration=durations)
    await message.channel.send(file=discord.File('chart.gif'))

def bezier(input):
    return input * input * (3.0 - 2.0 * input)

def tempered_bezier(input):
    return min(1.0, (bezier(input) * input) + (1.5 * input * (1.0 - input)))
