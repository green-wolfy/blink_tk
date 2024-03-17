import asyncio
from aiohttp import ClientSession
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load

import os
import sys

from tkinter import *
from tkinter import messagebox
import threading

cred_file = "./cred.json"
#blink_session = None

async def start():
    #global blink_session
    #blink_session = ClientSession()
    if os.path.isfile(cred_file):
        blink = Blink()
        #blink = Blink(session=blink_session) # this will invalid the credential json file as new session was created
        auth = Auth(await json_load(cred_file))
        blink.auth = auth
        await blink.start()
    else:
        #blink = Blink(session=blink_session)
        blink = Blink(session=ClientSession())
        #auth = Auth({"username": <your username>, "password": <your password>}, no_prompt=True) # may still need a code due to 2FA
        #blink.auth = auth
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

async def blink_main():
    blink = await start()
    for name, camera in blink.cameras.items():
        #print(name)                   # Name of the camera
        #print(camera.attributes)      # Print available attributes of camera
        #camera = blink.cameras['SOME CAMERA NAME']
        await pull(blink, camera)
    #await blink.auth.logout(blink) this doesn't help on the clean up issue, and would invalidate the credential json file
    #await blink_session.close() doesn't help either

def _asyncio_thread(async_loop):
    #asyncio.run(blink_main())
    try:
        async_loop.run_until_complete(blink_main())
        async_loop.stop()
        print("We are here!") # debug cleaning up issue after terminated
    finally:
        async_loop.close()

def do_freezed():
    messagebox.showinfo(message='Tkinter is reacting.')

if __name__ == '__main__':
    if len(sys.argv)>1:
        asyncio.run(blink_main())
    else:
        # refer to https://stackoverflow.com/questions/46727787/runtimeerror-there-is-no-current-event-loop-in-thread-in-async-apscheduler, has to create loop in main thread
        async_loop = asyncio.get_event_loop()
        root = Tk()
        Button(master=root, text='Asyncio Tasks', command= lambda: threading.Thread(target=_asyncio_thread, args=(async_loop,)).start()).pack()
        Button(master=root, text='Freezed???', command=do_freezed).pack()
        root.mainloop()
