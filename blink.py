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
    await camera.async_arm(True)  # Arm a sync. Same as: await blink.sync[camera.name].async_arm(True)
    await blink.refresh(force=True)  # force a cache update USE WITH CAUTION
    data_jpg = camera.image_from_cache  # bytes-like image object (jpg)
    data_vid = camera.video_from_cache  # bytes-like video object (mp4)
    if data_jpg: print("Cached %d bytes as jpg" % len(data_jpg))
    else: print("No jpg data")
    if data_vid: print("Cached %d bytes as video" % len(data_vid))
    else: print("No video data")
    #await camera.image_to_file('./image.jpg')
    #await camera.video_to_file('./video.mp4')
    sync = blink.sync[camera.name]
    print(f"{sync.name} status: {sync.arm}")

    #https://rest-u056.immedia-semi.com/api/v3/media/accounts/222219/networks/239481/owl/290887/thumbnail/thumbnail.jpg?ts=1669122404&ext=
    #{base_url}/api/v3/accounts/{account_id}/networks/{network_id}/sync_modules/{sync_id}/local_storage/manifest/{manifest_id}/clip/request/

async def main():
    blink = await start()
    for name, camera in blink.cameras.items():
        #print(name)                   # Name of the camera
        #print(camera.attributes)      # Print available attributes of camera
        #camera = blink.cameras['SOME CAMERA NAME']
        await pull(blink, camera)

asyncio.run(main())
