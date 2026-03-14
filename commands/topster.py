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
from pygifsicle import optimize

import urllib.parse


headers = {'Accept': 'application/json'}

async def topster(message, lastfmKey, spotifyKey):
    args = message.content.split(" ")[1:]

    if args[0] == "-orbit":
        await orbit_topster(message, lastfmKey, spotifyKey)
        return

    if len(args) > 0:
        user = args[0]
    else:
        await message.channel.send("Please specify a lastfm username.")
        return

    working = await message.channel.send("Working on it!")

    limit = 12
    total_limit = limit * limit

    if total_limit > 1000:
        await message.channel.send("Please select a smaller limit.")
        return

    period = "12month"
    r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user + '&limit=' + str(total_limit) + '&page=1&period=' + period +'&api_key=' + lastfmKey + '&format=json', headers=headers)
    rawjson = r.json()
    topalbums = rawjson['topalbums']['album']

    album_size = 170
    vert_offset = 32
    hor_offset = 32

    pad = 100

    h = (album_size + vert_offset) * limit + 2 * pad
    w = (album_size + hor_offset) * limit + 2 * pad
    image = np.zeros((h, w, 4), dtype = np.uint8)
    image2 = image.copy()

    # add blank square to center of image
    #image[int(h/2) - 2*album_size:int(h/2) + 2*album_size, int(w/2) - 2*album_size:int(w/2) + 2*album_size] = (0, 255, 0, 100)
    skipped_albums = 0

    albums = [None] * total_limit
    # multi-threaded to get all album covers first
    def place_album(x):
        index = x
        r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=' + user + '&limit=1&page=' + str(index + 1) + '&period=' + period +'&api_key=' + lastfmKey + '&format=json', headers=headers)
        # limit 50 per page and actually pull (x) / 1000 pages

        rawjson = r.json()
        msg = rawjson['topalbums']['album']

        if len(msg) == 0:
            return

        album = msg[0]
        print(index)
        print(album['name'])

        if len(album['image'][2]['#text']) > 0:
            init_im = requests.get(album['image'][2]['#text'])
            bytes_im = io.BytesIO(init_im.content)
            try:
                cv_im = Image.open(bytes_im)
            except PIL.UnidentifiedImageError:
                return
            cv_im = cv_im.convert("RGBA")
        else:
            return

        albums[x] = [album, cv_im]

    threads = [None] * 144
    # TODO too many threads causes issue

    # initialize threads
    # for i in range(min(len(threads), total_limit)):
    #     threads[i] = Thread(target=place_album, args=(i,))
    #     threads[i].start()
    #     print('Waiting for thread ' + str(i) + ' to finish...')
    #
    # album_count = 0
    # thread_index = 0
    # while album_count < total_limit:
    #     thread_index = thread_index % len(threads)
    #
    #     if not threads[thread_index].is_alive():
    #         threads[thread_index] = Thread(target=place_album, args=(album_count,))
    #         threads[thread_index].start()
    #         album_count += 1
    #
    #     thread_index += 1


    # create collage
    while True:
        await message.channel.send("New iteratioN! " + str(vert_offset))
        vert_offset += 3
        hor_offset += 3

        h = (album_size + vert_offset) * limit + 2 * pad
        w = (album_size + hor_offset) * limit + 2 * pad
        image = np.zeros((h, w, 4), dtype = np.uint8)

        # add blank square to center of image
        #image[int(h/2) - 2*album_size:int(h/2) + 2*album_size, int(w/2) - 2*album_size:int(w/2) + 2*album_size] = (0, 255, 0, 100)
        skipped_albums = 0

        for i in range(len(topalbums) - 1):
            if skipped_albums > 0:
                break

            if topalbums[i] is None:
                await message.channel.send("Skipped album " + str(i))
                continue

            album_name = topalbums[i]['name']
            print(album_name)


            if 'image' not in topalbums[i]:
                await message.channel.send("Skipped album " + album_name)
                continue

            if topalbums[i]['image'][2]['#text'] == "":
                await message.channel.send("Skipped album " + album_name)
                continue

            init_im = requests.get(topalbums[i]['image'][2]['#text'])

            bytes_im = io.BytesIO(init_im.content)
            try:
                cv_im = Image.open(bytes_im)
            except PIL.UnidentifiedImageError:
                return

            cv_im = cv_im.convert("RGBA")

            # map 0 - total_limit to 1.4 - 0.6
            scale = 0.8 * (1 - (i / (total_limit - 1))) + 0.6
            #scale = abs(np.random.normal(0.8, 0.2))
            #cv_im = rescale(cv_im, scale)
            cv_im = cv_im.resize((int(cv_im.size[0] * scale), int(cv_im.size[1] * scale)))
            cv_im2 = cv_im.copy()
            rotate_angle = random.randint(-5, 5)
            rotate_angle = random.randint(-5, 5)
            cv_im = cv_im.rotate(rotate_angle - 5, expand=True)
            cv_im2 = cv_im2.rotate(-rotate_angle + 5, expand=True)

            np_im = np.array(cv_im)
            np_im2 = np.array(cv_im2)
            size = np_im.shape[0]
            print(np_im.shape)
            print(album_size)

            dif = int((size - album_size) / 2)

            #add non-alpha to image
            mask = np_im[:, :, 3] != 0
            img_mask = np_im[mask]

            mask2 = np_im2[:, :, 3] != 0
            img_mask2 = np_im2[mask2]

            # try 5 times for best placement

            for attempt in range(100):
                print("Attempt " + str(attempt))
                #random placement
                x = random.randint(pad, image.shape[0] - pad - size)
                y = random.randint(pad, image.shape[1] - pad - size)

                region = image[x:x+size, y:y+size][mask]
                region2 = image2[x:x+size, y:y+size][mask]

                # count non-transparent pixels in region
                sum = np.count_nonzero(region[:, 3] > 0)
                print(sum)
                if sum > 3500:
                    continue
                else:
                    image[x:x+size, y:y+size][mask] = img_mask
                    image2[x:x+size, y:y+size][mask2] = img_mask2
                    skipped_albums -= 1
                    break

            skipped_albums += 1

            #image[i * (album_size + vert_offset) + pad:i * (album_size + vert_offset) + pad + size, j * (album_size + hor_offset) + pad:j * (album_size + hor_offset) + pad + size][mask] = img_mask

        if skipped_albums == 0:
            break


        # userColumn = np.vstack(columns)
        # image.append(userColumn)
        # image.append(np.zeros((174 * limit + 16 * limit, 32, 4), dtype = np.uint8))

    # lay background image

    # load background image
    back_small = Image.open(f"assets/topster_bg.jpeg")
    back_small = back_small.convert("RGBA")
    back_small = back_small.resize((image.shape[1], image.shape[0]), Image.Resampling.LANCZOS)
    canvas = np.array(back_small)
    canvas2 = np.array(back_small)
    #canvas = np.ones((image.shape[0], image.shape[1], 4), dtype=np.uint8) * 255

    mask = image[:, :, 3] > 125 # mostly visible
    img_mask = image[mask]
    mask2 = image2[:, :, 3] > 125 # mostly visible
    img_mask2 = image2[mask2]
    print(img_mask.shape)
    canvas[0:image.shape[0], 0:image.shape[1]][mask] = img_mask
    canvas2[0:image2.shape[0], 0:image2.shape[1]][mask2] = img_mask2


    # put nettspend in middle of canvas
    # nettspend = Image.open(f"assets/nettspend_trace.png")
    # nettspend = nettspend.convert("RGBA")
    # nettspend = nettspend.resize((int(3*album_size), int(3*album_size)), Image.Resampling.LANCZOS)
    # canvas[int(h/2) - int(1.5 * album_size):int(h/2) + int(1.5 * album_size), int(w/2) - int(1.5 * album_size):int(w/2) + int(1.5 * album_size)] = np.array(nettspend)

    # add user pfp to canvas
    r = requests.get('http://ws.audioscrobbler.com/2.0/?method=user.getinfo&user=' + user + '&api_key=' + lastfmKey + '&format=json', headers=headers)
    rawjson = r.json()
    pfp = rawjson['user']['image'][2]['#text']
    # if len(pfp) != 0:
    #     init_pfp = requests.get(pfp)
    #     bytes_pfp = io.BytesIO(init_pfp.content)
    #     cv_pfp = Image.open(bytes_pfp)
    #     cv_pfp = cv_pfp.convert("RGBA")
    #     cv_pfp = cv_pfp.resize((int(2*album_size), int(2*album_size)), Image.Resampling.LANCZOS)
    #     canvas[int(h/2) - int(album_size):int(h/2) + int(album_size), int(w/2) - int(album_size):int(w/2) + int(album_size)] = np.array(cv_pfp)

    #im = Image.fromarray(canvas)
    #im2 = Image.fromarray(canvas2)

    frames = [canvas, canvas2]

    #im.save("chart.png")
    imageio.mimsave('chart.gif', frames, loop=0, duration=1)

    await message.channel.send(file=discord.File('chart.gif'))
    await message.channel.send(f"Skipped {skipped_albums}/{total_limit} albums")
    await working.delete()

def rescale(img, factor):
    factor = min(factor, 1)
    width = int(img.size[0] * (1 / factor))
    height = int(img.size[1] * (1 / factor))
    canvas = np.zeros((height, width, 4), dtype=np.uint8)

    img_arr = np.array(img)

    # put img in center of canvas
    start_width = int((width - img_arr.shape[1]) / 2)
    start_height = int((height - img_arr.shape[0]) / 2)

    canvas[start_height:start_height + img_arr.shape[0], start_width:start_width + img_arr.shape[1]] = img_arr

    img_io = Image.fromarray(canvas)
    img_io = img_io.resize(img.size, Image.Resampling.LANCZOS)

    return img_io

async def orbit_topster(message, lastfmKey, spotifyKey):
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

    back_small = Image.open(f"assets/pvc_bg.png")
    back_small = back_small.convert("RGBA")
    back_small = back_small.resize((h, w), Image.Resampling.LANCZOS)
    canvas = np.array(back_small)
    #canvas = np.ones((h, w, 4), dtype=np.uint8) * 255

    top_text = Image.open(f"assets/pvc_text_20fps.gif")
    top_text_frames = top_text.n_frames

    images = [None] * total_limit

    topalbums = albums_from_playlist(message.content.split()[2], spotifyKey)

    albums_saved = 0
    i = 0
    albumnames = []
    while albums_saved < total_limit:

        album = topalbums[i]
        # if len(album['image'][2]['#text']) > 0:
        #     init_im = requests.get(album['image'][2]['#text'])
        #     bytes_im = io.BytesIO(init_im.content)
        #     cv_im = Image.open(bytes_im)
        #     cv_im = cv_im.resize((album_size, album_size))
        #     cv_im = cv_im.convert("RGBA")
        #     images[albums_saved] = cv_im
        #     albums_saved += 1

        name = album['track']['album']['name']
        print(name)

        if len(album['track']['album']['images']) == 0:
            await message.channel.send("Skipped album " + name)
            continue

        init_im = requests.get(album['track']['album']['images'][1]['url'])
        bytes_im = io.BytesIO(init_im.content)
        cv_im = Image.open(bytes_im)
        cv_im = cv_im.convert("RGBA")
        cv_im = cv_im.resize((album_size, album_size), Image.Resampling.LANCZOS)
        if name not in albumnames:
            images[albums_saved] = cv_im
            albums_saved += 1

            #await message.channel.send(name)
            #await message.channel.send(album['track']['album']['images'][1]['url'])

        albumnames.append(name)
        i += 1


    framerate = 20
    frames = []
    theta_offset = 0
    duration = 5

    for frame in range(framerate * duration):
        print(frame)
        f_canvas = canvas.copy()
        positions = []
        for ring in range(rings):
            print(ring)
            radius_mult_offset = abs(math.sin(frame * 1 / (framerate * duration) * 2 * math.pi))
            #radius = (ring * canvas_size/rings) / 2
            radius = ring * album_size + 40
            #radius = (ring * canvas_size/rings) / 2 * (0.2 + radius_mult_offset)
            #radius = (ring * canvas_size/rings) / 2 * (0.8 + radius_mult_offset * 0.4)
            positions.append([])
            num_albums = ring_lengths[ring]
            #ring_theta_offset = theta_offset / 2**(ring-1)  # farther out moves slower
            ring_theta_offset = -theta_offset
            #ring_theta_offset = 0
            for album in range(num_albums):
                position = (int(canvas_size/2) + radius * math.cos(album / num_albums * 2 * math.pi + ring_theta_offset),
                            int(canvas_size/2) + radius * math.sin(album / num_albums * 2 * math.pi + ring_theta_offset))
                positions[ring].append(position)

        album_index = 0
        for ring in positions:
            for pos in ring:
                #cv_im = cv_im.resize((album_size, album_size))
                cv_im = images[album_index]
                f_canvas[int(pos[0]) - int(album_size/2):int(pos[0]) + int(album_size/2), int(pos[1]) - int(album_size/2):int(pos[1]) + int(album_size/2)] = np.array(cv_im)

                album_index += 1
                #canvas[int(pos[0]) - 5:int(pos[0]) + 5, int(pos[1]) - 5:int(pos[1]) + 5] = (0, 0, 0, 255)

        theta_offset = (frame / (framerate * duration)) * 2 * math.pi

        # load pvc text on top with alpha mask
        # pvc_text = Image.open(f"assets/pvc_logo_text.png")
        # pvc_text = pvc_text.convert("RGBA")
        # pvc_text = pvc_text.resize((canvas_size, canvas_size), Image.Resampling.LANCZOS)
        # pvc_text_mask = np.array(pvc_text)[:, :, 3] != 0
        #
        # f_canvas[0:canvas_size, 0:canvas_size][pvc_text_mask] = np.array(pvc_text)[pvc_text_mask]

        # crop frames
        #f_canvas = f_canvas[int(canvas_size/2) - 500:int(canvas_size/2) + 500, int(canvas_size/2) - 500:int(canvas_size/2) + 500]

        # load given frame of animated pvc text
        closest_index = int((frame / (framerate * duration)) * top_text_frames)
        top_text.seek(closest_index)
        top_text_frame = top_text.convert("RGBA")
        top_text_frame = top_text_frame.resize((canvas_size, canvas_size), Image.Resampling.LANCZOS)
        top_text_frame_mask = np.array(top_text_frame)[:, :, 3] != 0

        f_canvas[0:canvas_size, 0:canvas_size][top_text_frame_mask] = np.array(top_text_frame)[top_text_frame_mask]

        # resize to 512x512
        f_canvas = Image.fromarray(f_canvas)
        f_canvas = f_canvas.resize((512, 512), Image.Resampling.LANCZOS)
        f_canvas = np.array(f_canvas)

        frames.append(f_canvas)

    imageio.mimsave('chart.gif', frames, loop=0, duration=0.5, fps=framerate)
    # optimize('chart.gif')
    # im = Image.fromarray(canvas)
    # im.save("chart.png")

    await message.channel.send(file=discord.File('chart.gif'))

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

        print(name)

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
    print(len(albumcovers), size)
    blank_albums = size*size - len(albumcovers)

    image = []
    rows = []

    for i in range(len(albumcovers)):
        album = albumcovers[i]

        album_pad = np.zeros((320, 320, 4), dtype=np.uint8)
        album_pad[10:310, 10:310] = np.array(album)
        album = Image.fromarray(album_pad)

        print(album.size)
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

    print([print(x.shape) for x in image])
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


    await message.channel.send(file=discord.File('chart.png'))
    await message.channel.send(file=discord.File('text.png'))

def albums_from_playlist(playlist: str, spotifyKey: str) -> list:
    topalbums = []

    playlist_id = re.search("(?!$)[a-zA-Z0-9]{10,}", playlist).group(0)

    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + spotifyKey}
    fields = "total"
    #fields = "items.track.album(name, images, artists, preview_url)"
    r = requests.get('https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks?limit=100&fields=' + fields, headers=headers)
    print(r.content)
    print(r.text)
    rawjson = r.json()
    print(rawjson)

    total = rawjson['total']
    iterations = math.ceil(total / 100)  # for max_limit of 100

    #fields = "items.track.album(name, images, artists, preview_url)"
    fields = "items.track.album(name, images, artists)"

    for i in range(iterations):
        r = requests.get('https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks?limit=100&offset=' + str(i*100) + '&fields=' + fields, headers=headers)
        rawjson = r.json()
        print(rawjson)
        topalbums.extend(rawjson['items'])

    return topalbums

def albums_from_user(message, spotifyKey: str) -> list:
    topalbums = []

    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + spotifyKey}
    r = requests.get('https://api.spotify.com/v1/me/albums', headers=headers)
    print(r.text)
    rawjson = r.json()
    print(rawjson)

    total = rawjson['total']
    iterations = math.ceil(total / 50)  # for max_limit of 100

    for i in range(iterations):
        r = requests.get('https://api.spotify.com/v1/me/albums?limit=50&offset=' + str(i*50), headers=headers)
        print(r)
        rawjson = r.json()
        print(rawjson)
        topalbums.extend(rawjson['items'])
    #
    # for album in topalbums:
    #     name = album['album']['name']
    #     artist = ", ".join([artist['name'] for artist in album['album']['artists']])
    #     #await message.channel.send(artist + " - " + name)

    return topalbums
