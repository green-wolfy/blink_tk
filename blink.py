import asyncio
from aiohttp import ClientSession
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load

import os

cred_file = "./cred.json"

async def start():
    if os.path.isfile(cred_file):
        blink = Blink()
        auth = Auth(await json_load(cred_file))
        blink.auth = auth
        await blink.start()
    else:
        blink = Blink(session=ClientSession())
        await blink.start()
        if blink: await blink.save(cred_file)
    return blink

async def pull(blink, camera):
    await blink.refresh(force=True)  # force a cache update USE WITH CAUTION
    data_jpg = camera.image_from_cache  # bytes-like image object (jpg)
    data_vid = camera.video_from_cache  # bytes-like video object (mp4)
    if data_jpg: print("Cached %d bytes as jpg" % len(data_jpg))
    else: print("No jpg data")
    if data_vid: print("Cached %d bytes as video" % len(data_vid))
    else: print("No video data")

async def main():
    blink = await start()
    for name, camera in blink.cameras.items():
        #print(name)                   # Name of the camera
        #print(camera.attributes)      # Print available attributes of camera
        #camera = blink.cameras['SOME CAMERA NAME']
        await pull(blink, camera)

asyncio.run(main())
