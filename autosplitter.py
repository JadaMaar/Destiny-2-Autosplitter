import json
import threading as th
import time
from datetime import datetime
from socket import socket

import mss
import numpy as np
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
import cv2

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

# boss hp bar
boss_hp_box = {"top": 978, "left": 645, "width": 10, "height": 5}

# wipe screen
light_fading_box = {"top": 100, "left": 400, "width": 200, "height": 70}

# joining allies
joining_allies_box = {"top": 815, "left": 805, "width": 140, "height": 28}

screenshot_boxes = [prompt_box, restricted_box, new_objective_box, mission_complete_box, objective_complete_box]

# pytesseract installation path
path_to_tesseract = r"G:\Program Files\Tesseract-OCR\tesseract.exe"
# pytesseract.tesseract_cmd = path_to_tesseract
api = tesserocr.PyTessBaseAPI(lang="eng")
# reader = easyocr.Reader(['en'], gpu=True)
# api.SetPageSegMode(tesserocr.PSM.SINGLE_LINE)

is_running = False
next_split = False
# this is set True if the next Split splits on the same input as the current one. in this case there will be a downtime
# before it will check for the next screenshot to avoid double splitting on one pic
dupe_split = False
block_screenshots = False
# activates ocr for objective splits while true
objective_flash = False
# min ratio to check for text
ratio_threshold = 0.3

delta = 0.0
avg_fps = 0
fps_cap = 100
threads_list = []

# split variables
split_index = 0
reset = False
autosplit = False


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
            elif current_split[0] == "Boss Spawn":
                check_boss(current_split[1], True)
            elif current_split[0] == "Boss Dead":
                check_boss(current_split[1], False)
            elif current_split[0] == "Wipe Screen":
                check_wipe_screen()
            elif current_split[0] == "Joining Allies":
                check_joining()
            else:
                check_custom_prompt(current_split[0])
            next_time = datetime.now().timestamp()
            delta = (next_time - current_time)
            if delta < (1 / fps_cap):
                time.sleep((1 / fps_cap) - delta)
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
    # if is_running:
    #     start_auto_splitter_thread(splits_copy)


def stop_auto_splitter():
    global is_running, next_split
    is_running = False
    next_split = False


def take_screenshot(area):
    sct_img = sct.grab(area)
    img = Image.new("RGB", sct_img.size)
    pixels = zip(sct_img.raw[2::4], sct_img.raw[1::4], sct_img.raw[::4])
    img.putdata(list(pixels))

    # turn and crop image for better screenshot
    # if area == prompt_box:
    #     img = img.rotate(-3, resample=Image.BICUBIC, expand=True)
    #     img = img.crop((7, 16, 370, 35))

    # convert image to greyscale and apply threshold

    # if area in [new_objective_box, objective_complete_box]:
    #     img = img.convert('L')
    #     img = np.array(img)
    #     # TODO: test other thresh modes
    #     im_bw = cv2.threshold(img, 230, 255, cv2.THRESH_TOZERO)[1]
    #     img = Image.fromarray(im_bw)

    return img


def check_text(target_text, img, dummy):
    global next_split, dupe_split, block_screenshots, autosplit
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
            autosplit = True
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
    global objective_flash
    img = take_screenshot(new_objective_box)
    ratio = get_bw_ratio(img)
    # if not objective_flash and ratio > ratio_threshold:
    #     objective_flash = True
    #     th.Timer(1, set_objective_flash).start()
    # if objective_flash:
    check_text("NEW OBJECTIVE", img, dummy)


def get_bw_ratio(img):
    img1 = np.array(img)
    number_of_white_pix = np.sum(img1 > 0)  # extracting only white pixels
    number_of_black_pix = np.sum(img1 == 0)  # extracting only black pixels
    if number_of_black_pix == 0:
        number_of_black_pix = 1
    ratio = number_of_white_pix / number_of_black_pix
    return ratio


def set_objective_flash():
    global objective_flash
    objective_flash = False


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
    # if not is_player_prompt(img):
    #     print("CHECK")
    check_text(prompt, img, False)


def check_boss(dummy, spawn):
    global autosplit, block_screenshots, next_split

    img = take_screenshot(boss_hp_box)
    # img.show()
    light_orange = (1, 155, 155)
    dark_orange = (25, 255, 255)
    img1 = np.array(img)
    hsv_img = cv2.cvtColor(img1, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv_img, light_orange, dark_orange)
    result = cv2.bitwise_and(img1, img1, mask=mask)
    # img = Image.fromarray(result)
    # img.show()

    number_of_black_pix = np.sum(result == 0)
    other_pixel = np.sum(result != 0)
    ratio = number_of_black_pix / (number_of_black_pix + other_pixel)

    # if less than 10% of the pixel are black the boss is spawned and more than 80% he's basically dead TODO: adjust value
    if spawn:
        check = ratio < 0.1
    else:
        check = ratio > 0.8

    if check:
        if not dummy:
            # pyautogui.press('num1')
            l.startOrSplit()
            autosplit = True
        if dupe_split:
            block_screenshots = True
            th.Timer(6, set_next_split).start()
        else:
            next_split = False


def check_wipe_screen():
    # TODO: back2back wipescreen arent properly handled duration is variable and server dependend
    img = take_screenshot(light_fading_box)
    check_text("your", img, False)


def check_joining():
    img = take_screenshot(joining_allies_box)
    check_text("joining", img, False)


# returns whether the message in the prompt box was made by the player e.g. created orbs
def is_player_prompt(img: Image):
    # TODO: change the 7 to work for non 1080p monitors
    triangle = img.crop((7, 12, prompt_box["width"] / 20, prompt_box["height"])).convert('L')
    # triangle.show()
    # img = img.convert('L')
    img = np.array(triangle)
    # TODO: test other thresh modes
    im_bw = cv2.threshold(img, 100, 255, cv2.THRESH_OTSU)[1]
    # img = Image.fromarray(im_bw)
    # img.show()
    # ratio = get_bw_ratio(img)
    # print(f"bw ratio: {ratio}")
    # return ratio > 0.2
    canny = cv2.Canny(im_bw, 240, 255)
    contours, hier = cv2.findContours(canny, 1, 2)
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
        print(f"approx: {len(approx)}")
        if len(approx) == 3:
            cv2.drawContours(im_bw, [cnt], 0, (0, 255, 0), 2)
            tri = approx
    img = Image.fromarray(im_bw)
    img.show()
    # using a findContours() function
    # _, thrash = cv2.threshold(img, 240, 255, cv2.CHAIN_APPROX_NONE)
    # contours, _ = cv2.findContours(thrash, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # for contour in contours:
    #     approx = cv2.approxPolyDP(contour, .03 * cv2.arcLength(contour, True), True)
    #     print(f"approx: {len(approx)}")


# start_auto_splitter(run_splits)
def get_main_monitor():
    for m in get_monitors():
        if m.is_primary:
            return m


def get_hotkeys():
    global autosplit, split_index
    livesplit = l.getSocket()# socket()
    # livesplit.connect(("localhost", 16834))
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
    prev_index = -1
    while True:
        try:
            livesplit.send("getsplitindex\r\n".encode())
            current_index = livesplit.recv(1024).decode()[:-2]
            if not autosplit:
                if current_index == -1:
                    split_index = 0
                if current_index != prev_index:
                    print(current_index)
                    prev_index = current_index
                    split_index += 1
            # print("STUFF HAPPENS")
            # if data:
            #     event = data
            #     if "split" in event:
            #         print("Split triggered!")
        except:
            print("timeout")
            pass


def test():
    thread = th.Thread(target=get_hotkeys)
    thread.start()


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
