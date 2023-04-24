import json
import threading as th
import time
from datetime import datetime
from socket import socket

import mss
import psutil
import pyautogui
import tesserocr
import torch
from PIL import Image
from screeninfo import get_monitors
import subprocess
import multiprocessing as mp
from autocorrect import Speller
import livesplit
import requests
import keyboard
import os
import ctypes

print("CUDA AVAILABLE: " + str(torch.version.cuda))
print(tesserocr.tesseract_version())
sct = mss.mss()
spell = Speller()
l = livesplit.Livesplit()

# box that checks the content of the current prompt in the bottom left corner
prompt_box = {"top": 825, "left": 40, "width": 370, "height": 35}

# box that checks respawn restricted
restricted_box = {"top": 460, "left": 840, "width": 240, "height": 30}

# new objective box
new_objective_box = {"top": 265, "left": 190, "width": 200, "height": 30}

# new objective box
objective_complete_box = {"top": 265, "left": 155, "width": 260, "height": 30}

# mission complete box
mission_complete_box = {"top": 70, "left": 190, "width": 660, "height": 70}

screenshot_boxes = [prompt_box, restricted_box, new_objective_box, mission_complete_box, objective_complete_box]

# pytesseract installation path
path_to_tesseract = r"G:\Program Files\Tesseract-OCR\tesseract.exe"
# pytesseract.tesseract_cmd = path_to_tesseract
api = tesserocr.PyTessBaseAPI(lang="eng")
# reader = easyocr.Reader(['en'], gpu=True)
api.SetPageSegMode(tesserocr.PSM.SINGLE_LINE)

is_running = False
next_split = False
# this is set True if the next Split splits on the same input as the current one. in this case there will be a downtime
# before it will check for the next screenshot to avoid double splitting on one pic
dupe_split = False
block_screenshots = False

delta = 0.0
avg_fps = 0
fps_cap = 100
threads_list = []

# split variables
split_index = 0
reset = False


def start_auto_splitter_thread(splits):
    split_thread = th.Thread(target=start_auto_splitter, args=(splits,))
    split_thread.start()


def read_image(q: mp.Queue):
    while True:
        if not q.empty():
            img = q.get_nowait()
            q.task_done()
            check_text("NEW", img, False)


def start_auto_splitter(splits):
    global is_running, next_split, dupe_split, delta, avg_fps, split_index, reset
    is_running = True
    count = 0
    total = 0
    split_index = 0
    next_split = False
    current_split = ""
    splits_copy = splits.copy()
    current_time = datetime.now().timestamp()
    while is_running:
        #####
        if reset:
            reset = False
            break
        #####
        if not next_split:
            next_split = True
            if len(splits) > split_index:
                current_split = splits[split_index]
                print("CURRENT SPLIT: " + str(current_split))
                split_index += 1
                if len(splits) > split_index:
                    dupe_split = current_split[0] == splits[split_index][0]
                    print("NEXT SPLIT: " + str(splits[split_index][0]))
                else:
                    dupe_split = False
            else:
                break
        if not block_screenshots:
            if current_split[0] == "New Objective":
                check_new_objective(current_split[1])
            elif current_split[0] == "Objective Complete":
                check_objective_complete(current_split[1])
            elif current_split[0] == "Respawning Restricted":
                check_darkness_zone(current_split[1])
            elif current_split[0] == "Access Granted":
                check_access_granted(current_split[1])
            elif current_split[0] == "Mission Completed":
                check_mission_complete(current_split[1])
            else:
                check_custom_prompt(current_split[0])
            # next_time = datetime.now().timestamp()
            # delta = (next_time - current_time)
            # if delta < (1 / fps_cap):
            #     time.sleep((1 / fps_cap) - delta)
            next_time = datetime.now().timestamp()
            delta = (next_time - current_time)
            current_time = datetime.now().timestamp()
            if delta != 0:
                fps = 1 / delta
                count += 1
                total += fps
            if count != 0:
                avg_fps = (total / count)
            # print(avg_fps)
            # print(f"CPU usage: {psutil.cpu_percent()}")
    if is_running:
        start_auto_splitter_thread(splits_copy)


def stop_auto_splitter():
    global is_running, next_split
    is_running = False
    next_split = False


def take_screenshot(area):
    sct_img = sct.grab(area)
    img = Image.new("RGB", sct_img.size)
    pixels = zip(sct_img.raw[2::4], sct_img.raw[1::4], sct_img.raw[::4])
    img.putdata(list(pixels))
    # img = img.resize((img.width * 2, img.height * 2))
    # img = img.rotate(-3, resample=Image.BICUBIC, expand=True)
    # img = img.convert("L")
    # img.save("test.png")
    # img.show()

    # convert image to greyscale
    img = img.convert('L')
    # width, height = img.size
    # binary_image(img, 0, width, 0, height)
    # img.save("test.png")
    return img


def binary_image(img, x_start, x_end, y_start, y_end):
    thresh = 200
    # traverse through pixels
    for x in range(x_start, x_end):
        for y in range(y_start, y_end):

            # if intensity less than threshold, assign white
            if img.getpixel((x, y)) < thresh:
                img.putpixel((x, y), 0)

            # if intensity greater than threshold, assign black
            else:
                img.putpixel((x, y), 255)


def check_text(target_text, img, dummy):
    global next_split, dupe_split, block_screenshots
    target_text = target_text.lower()

    # tesserocr implementation
    api.SetImage(img)
    text = api.GetUTF8Text()

    # tesseract form commandline
    # text = subprocess.Popen([
    #     "tesseract",
    #     "temp.png",
    #     "-"
    # ]).communicate()[0]

    # easyocr implementation
    # img = np.array(img)
    # text = reader.readtext(img, paragraph=True)
    # if len(text) > 0:
    #     text = text[0][1]
    # else:
    #     text = ""

    # pytesseract implementation
    # text = tesserocr.image_to_text(img, oem=3)
    text = str(text).lower()
    # text = spell(text)
    # print("TEXT: " + str(text))
    # text = "njogrsnognoprts"
    if target_text in text:
        # print("TRIGGER")
        if not dummy:
            # pyautogui.press('num1')
            l.startOrSplit()
        if dupe_split:
            block_screenshots = True
            th.Timer(6, set_next_split).start()
        else:
            next_split = False
    # break


def set_next_split():
    global next_split, block_screenshots
    next_split = False
    block_screenshots = False


def check_new_objective(dummy):
    img = take_screenshot(new_objective_box)
    """"
    w, h = img.size
    # split image in 3 parts
    im1 = img.crop((0, 0, w//3, h))
    im2 = img.crop((w//3, 0, 2 * w//3, h))
    im3 = img.crop((2 * w//3, 0, w, h))
    im1.show()
    im2.show()
    im3.show()
    splits = [im1, im2, im3]
    pool = mp.Pool(processes=1)
    pool.map(get_text, splits)
    pool.close()
    """
    check_text("NEW", img, dummy)


def check_objective_complete(dummy):
    img = take_screenshot(objective_complete_box)
    check_text("COMPLETE", img, dummy)


def get_text(img):
    api.SetImage(img)
    text = api.GetUTF8Text()
    # q.put(text.lower())
    # print(f"GET_TEXT: {text.lower()}")
    return text.lower()


def check_darkness_zone(dummy):
    img = take_screenshot(restricted_box)
    check_text("Respawning Restricted", img, dummy)


def check_mission_complete(dummy):
    img = take_screenshot(mission_complete_box)
    check_text("MISSION", img, dummy)


def check_access_granted(dummy):
    check_custom_prompt("Access Granted")


def check_custom_prompt(prompt):
    img = take_screenshot(prompt_box)
    check_text(prompt, img, False)


# start_auto_splitter(run_splits)
def get_main_monitor():
    for m in get_monitors():
        if m.is_primary:
            return m


""""
def get_hotkeys():
    livesplit = socket()
    livesplit.connect(("localhost", 16834))
    # livesplit.send("initgametime\r\n".encode())
    # livesplit.send("setcomparison gametime\r\n".encode())
    # livesplit.send("starttimer\r\n".encode())
    # livesplit.send("pausegametime\r\n".encode())
    # time.sleep(3)
    # livesplit.send("startorsplit\r\n".encode())
    # ls_time = livesplit.recv(1024).decode()[:-2]
    # print("reply: " + ls_time)
    # Listen for events
    # livesplit.settimeout(1)
    while True:
        try:
            data = livesplit.recv(1024).decode()[:-2]
            print("STUFF HAPPENS")
            if data:
                event = data
                if "split" in event:
                    print("Split triggered!")
        except:
            print("timeout")
            pass
"""


def monitor_setup():
    main_monitor = get_main_monitor()
    width = main_monitor.width
    height = main_monitor.height
    x_modifier = width / 1920
    y_modifier = height / 1080
    for box in screenshot_boxes:
        box["left"] = int(box["left"] * x_modifier)
        box["top"] = int(box["top"] * y_modifier)
        box["width"] = int(box["width"] * x_modifier)
        box["height"] = int(box["height"] * y_modifier)
    print(screenshot_boxes)


# handle hotkeys
def handle_split():
    global split_index
    # if event.name == "num 1":
    print("NUMPAD 1")
    livesplit = socket()
    livesplit.connect(("localhost", 16834))
    livesplit.send("getsplitindex\r\n".encode())
    ls_index = livesplit.recv(1024).decode()[:-2]
    print("reply: " + ls_index)
    livesplit.close()
    # not incrementing if result is 0 or -1
    # 0 means the timer was just started and -1 that the splits got reset by pressing split button after a finished run
    if ls_index not in ["0", "-1"]:
        split_index += 1


def handle_reset():
    global reset
    reset = True
    print("NUMPAD 3")


keyboard.add_hotkey("num 1", handle_split)
keyboard.add_hotkey("num 3", handle_reset)
