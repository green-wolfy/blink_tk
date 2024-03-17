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

async def shot(blink, camera):
    print("Taking snapshot")
    # Trigger a snapshot
    await camera.snap_picture()
    # Wait for the snapshot to be taken
    await asyncio.sleep(3)
    # Refresh the Blink system to get the new snapshot
    #await blink.refresh(force=True)
    # Save the snapshot to a file
    #await camera.image_to_file('./snapshot.jpg')
    print("Snapshot taken")

async def pull(blink, camera, render=None):
    print("Pulling data")
    await camera.async_arm(True)  # Arm a sync. Same as: await blink.sync[camera.name].async_arm(True)
    await blink.refresh(force=True)  # force a cache update USE WITH CAUTION
    data_jpg = camera.image_from_cache  # bytes-like image object (jpg)
    data_vid = camera.video_from_cache  # bytes-like video object (mp4)
    if data_jpg:
        await camera.image_to_file('./image.jpg') # for debugging
        if render!=None: render(data_jpg)
        else: print("Cached %d bytes as jpg" % len(data_jpg))
    else: print("No jpg data")
    if data_vid: print("Cached %d bytes as video" % len(data_vid))
    else: print("No video data")
    #await camera.image_to_file('./image.jpg')
    #await camera.video_to_file('./video.mp4')
    #sync = blink.sync[camera.name]
    #print(f"{sync.name} status: {sync.arm}")
    print("Data pulled")

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

''' Having tk loop with async function is a bit tricky. __init__ cannot be declared as async, and async function cannot be called directly from tk.
    The solution is to create a separate thread to run the async. The thread will create an event loop and run the async function in the loop.
    Refer to https://stackoverflow.com/questions/47895765/use-asyncio-and-tkinter-or-another-gui-lib-together-without-freezing-the-gui
'''
class blink_viewer:
    def __init__(self, master=None, loop=None):
        self.async_loop = loop
        # create a queue for tk to communicate with the asyncio thread
        self.queue = asyncio.Queue()
        self.worker = threading.Thread(target=self._asyncio_thread, args=(loop,)).start()
        Button(master=master, text='Snapshot', command=self.snapshot).pack()
        Button(master=master, text='View', command=self.view).pack()
        # show image view
        self.canvas = Canvas(master=master, width=640, height=480)
        self.canvas.pack()
        master.bind('<Destroy>', self.stop_worker)

    def view_image(self, data):
        print("Viewing image")
        '''#img = PhotoImage(data=data)
        img = Image.open('./image.jpg')
        # Convert the image to a format Tkinter can use
        photo = IMAGETEXT.PhotoImage(img)
        self.canvas.create_image(0, 0, image=img, anchor=NW)
        self.canvas.image = img'''

    def stop_worker(self, event=None):
        print("Stopping worker")
        self.queue.put_nowait('exit')
        #wait for the worker to finish
        if self.worker:
            self.worker.join()
            self.worker = None # avoid calling join again. However, still see this got called about 4 times. Why?
            self.async_loop.stop()  # the async might get stuck, so force stop it
            self.async_loop.close()

    async def worker_loop(self):
        self.blink = await start()
        # start message processing loop
        while True:
            # wait for a message from the tk thread
            message = await self.queue.get()
            print("Received message: %s" % message)
            if message == 'snapshot':
                await self.async_snapshot('shot')
            elif message == 'view':
                await self.async_snapshot('view')
            elif message == 'exit':
                break
            print("Message processed")

    async def async_snapshot(self, action='view'):
        for name, camera in self.blink.cameras.items():
            #print(name)                   # Name of the camera
            #print(camera.attributes)      # Print available attributes of camera
            #camera = blink.cameras['SOME CAMERA NAME']
            if action=='view': await pull(self.blink, camera, self.view_image)
            elif action=='shot': await shot(self.blink, camera)

    def _asyncio_thread(self, async_loop):
        try:
            async_loop.run_until_complete(self.worker_loop())
            async_loop.stop()
        finally:
            async_loop.close()

    def snapshot(self):
        print("Sending snapshot message")
        if self.blink:
            self.queue.put_nowait('snapshot')
        else:
            messagebox.showinfo("Error", "Blink not connected")

    def view(self):
        if self.blink:
            print("Sending view message")
            self.queue.put_nowait('view')
        else:
            messagebox.showinfo("Error", "Blink not connected")

if __name__ == '__main__':
    if len(sys.argv)>1:
        asyncio.run(blink_main())
    else:
        # refer to https://stackoverflow.com/questions/46727787/runtimeerror-there-is-no-current-event-loop-in-thread-in-async-apscheduler, has to create loop in main thread
        async_loop = asyncio.get_event_loop()
        root = Tk()
        blink_viewer(root, async_loop)
        root.mainloop()
