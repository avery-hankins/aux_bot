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
    limit = 25

    red_square = np.zeros((1000, 1000, 4), dtype=np.uint8)
    red_square[350:650, 350:650, 0] = 255
    red_square[350:650, 350:650, 3] = 255

    blue_square = np.zeros((1000, 1000, 4), dtype=np.uint8)
    blue_square[350:650, 350:650, 2] = 255
    blue_square[350:650, 350:650, 3] = 255

    covers = []
    names = []
    artists = []

    r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user + '&limit=' + str(limit) + '&period=' + period + '&api_key=' + lastfmKey + '&format=json', headers=headers)
    rawjson = r.json()
    albums = rawjson['topalbums']['album']

    blank = np.zeros((1000, 1000, 4), dtype=np.uint8)
    for album in albums:
        name = album['name']
        artist = album['artist']['name']
        print(name)

        if len(album['image'][2]['#text']) == 0:
            await message.channel.send("Skipped album " + name)
            continue

        names.append(name)
        artists.append(artist)

        init_im = requests.get(album['image'][2]['#text'])
        bytes_im = io.BytesIO(init_im.content)
        cv_im = Image.open(bytes_im)
        cv_im = cv_im.convert("RGBA")
        cv_im = cv_im.resize((300, 300), Image.Resampling.LANCZOS)
        blank[350:650, 350:650] = np.array(cv_im)
        covers.append(blank.copy())

    canvas = np.zeros((1000, 1000, 4), dtype=np.uint8)
    #canvas[350:650, 350:650] = red_square
    canvas[:, :, 3] = 255

    frames = []
    durations = []

    identity_matrix = np.array([[1, 0, 0],
                                [0, 1, 0],
                                [0, 0, 1]], dtype=np.float32)

    pts1 = np.float32([[350, 350], [650, 350], [350, 650], [650, 650]])
    pts2 = np.float32([[1000-163, 320], [1000-295, 415], [1000-163, 680], [1000-295, 585]])

    pts2_start = np.float32([[1000-295, 415], [1000-163, 320], [1000-295, 585], [1000-163, 680]])
    M_start = cv2.getPerspectiveTransform(pts1, pts2_start)
    M = cv2.getPerspectiveTransform(pts1, pts2_start)

    for cover in range(len(covers)):
        prev_cover = covers[cover - 1] if cover > 0 else covers[-1]
        prev_cover = np.flip(prev_cover, axis=1)
        current_cover = covers[cover]
        current_cover = np.flip(current_cover, axis=1)
        next_cover = covers[(cover + 1) % len(covers)]
        next_next_cover = covers[(cover + 2) % len(covers)]

        transform_frames = 60
        for i in range(transform_frames):
            percent_transform = bezier(i / (1.0 * transform_frames))
            #percent_transform_r = min(1.0, bezier(i / (1.0 * transform_frames)) * 1.5)
            percent_transform_r = tempered_bezier(i / (1.0 * transform_frames))
            print(percent_transform)

            # frame_theta = percent_transform * 1 * (math.pi / 180)
            #
            # frame_matrix = np.array([[math.cos(frame_theta), 0, math.sin(frame_theta)],
            #                          [0, 1, 0],
            #                          [-math.sin(frame_theta), 0, math.cos(frame_theta)]], dtype=np.float32)

            frame_M = percent_transform_r * M + (1 - percent_transform_r) * identity_matrix
            frame_M_start = percent_transform * identity_matrix + (1 - percent_transform) * M_start

            red_square_t = cv2.warpPerspective(current_cover, frame_M, (1000, 1000))
            red_square_t = np.flip(red_square_t, axis=1)
            blue_square_t = cv2.warpPerspective(next_cover, frame_M_start, (1000, 1000))

            next_red_square = cv2.warpPerspective(next_next_cover, M_start, (1000, 1000))
            next_red_square = next_red_square * percent_transform_r

            prev_blue_square = cv2.warpPerspective(prev_cover, M_start, (1000, 1000))
            prev_blue_square = np.flip(prev_blue_square, axis=1)

            mask = prev_blue_square[:, :, 3] != 0
            img_mask = prev_blue_square[mask]
            canvas_t = canvas.copy()
            canvas_t[mask] = img_mask

            mask = red_square_t[:, :, 3] != 0
            img_mask = red_square_t[mask]
            canvas_t[mask] = img_mask

            mask = next_red_square[:, :, 3] != 0
            img_mask = next_red_square[mask]
            canvas_t[mask] = img_mask

            mask = blue_square_t[:, :, 3] != 0
            img_mask = blue_square_t[mask]
            canvas_t[mask] = img_mask

            canvas_t = canvas_t[250:800, 150:850]

            frames.append(canvas_t)
            durations.append(25)

        red_square_t = cv2.warpPerspective(current_cover, M, (1000, 1000))
        red_square_t = np.flip(red_square_t, axis=1)
        blue_square_t = cv2.warpPerspective(next_cover, identity_matrix, (1000, 1000))
        next_red_square = cv2.warpPerspective(next_next_cover, M, (1000, 1000))

        prev_mask = red_square_t[:, :, 3] != 0
        current_mask = blue_square_t[:, :, 3] != 0
        next_mask = next_red_square[:, :, 3] != 0

        canvas_final = canvas.copy()
        canvas_final[prev_mask] = red_square_t[prev_mask]
        canvas_final[current_mask] = blue_square_t[current_mask]
        canvas_final[next_mask] = next_red_square[next_mask]

        canvas_final = Image.fromarray(canvas_final)

        still_text = ImageDraw.Draw(canvas_final)
        cover = cover + 1 if cover < len(covers) - 1 else 0
        still_text.text((500, 700), names[cover], font=ImageFont.truetype("assets/Andale Mono.ttf", 30), fill=(255,255,255), anchor="mm")
        still_text.text((500, 750), artists[cover], font=ImageFont.truetype("assets/Andale Mono.ttf", 30), fill=(255,255,255), anchor="mm")
        canvas_final = np.array(canvas_final)

        canvas_final = canvas_final[250:800, 150:850]

        frames.append(canvas_final)
        durations.append(1500)

    imageio.mimsave('chart.gif', frames, loop=0, duration=durations)
    await message.channel.send(file=discord.File('chart.gif'))

def bezier(input):
    return input * input * (3.0 - 2.0 * input)

def tempered_bezier(input):
    return min(1.0, (bezier(input) * input) + (1.5 * input * (1.0 - input)))
