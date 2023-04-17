import os
import threading as th
import time

import mss
import pyautogui
import tesserocr
from PIL import Image
from pynput.keyboard import Controller
from screeninfo import get_monitors

import main

sct = mss.mss()

# box that checks the content of the current prompt in the bottom left corner
prompt_box = {"top": 825, "left": 40, "width": 370, "height": 35}

# box that checks respawn restricted
restricted_box = {"top": 460, "left": 840, "width": 240, "height": 30}

# new objective box
new_objective_box = {"top": 265, "left": 190, "width": 200, "height": 30}

# mission complete box
mission_complete_box = {"top": 70, "left": 190, "width": 660, "height": 70}

screenshot_boxes = [prompt_box, restricted_box, new_objective_box, mission_complete_box]

# pytesseract installation path
path_to_tesseract = r"G:\Program Files\Tesseract-OCR\tesseract.exe"
# pytesseract.tesseract_cmd = path_to_tesseract
api = tesserocr.PyTessBaseAPI(psm=tesserocr.PSM.SINGLE_COLUMN, lang="des")

keyboard = Controller()

is_running = False
next_split = False
# this is set True if the next Split splits on the same input as the current one. in this case there will be a downtime
# before it will check for the next screenshot to avoid double splitting on one pic
dupe_split = False
block_screenshots = False

delta = 0.0
avg_fps = 0


def start_auto_splitter_thread(splits):
    split_thread = th.Thread(target=start_auto_splitter, args=(splits,))
    split_thread.start()


def start_auto_splitter(splits):
    global is_running, next_split, dupe_split, delta, avg_fps
    is_running = True
    os.environ['OMP_THREAD_LIMIT'] = '1'
    count = 0
    total = 0
    next_split = False
    current_split = ""
    splits_copy = splits.copy()
    while is_running:
        #####
        current_time = time.time()
        #####
        if not next_split:
            next_split = True
            if len(splits) > 0:
                current_split = splits.pop(0)
                if len(splits) > 0:
                    dupe_split = current_split[0] == splits[0][0]
                else:
                    dupe_split = False
            else:
                break
        if not block_screenshots:
            if current_split[0] == "New Objective":
                check_new_objective(current_split[1])
            elif current_split[0] == "Respawning Restricted":
                check_darkness_zone(current_split[1])
            elif current_split[0] == "Access Granted":
                check_access_granted(current_split[1])
            elif current_split[0] == "Mission Completed":
                check_mission_complete(current_split[1])
            else:
                check_custom_prompt(current_split[0])
        next_time = time.time()
        delta = (next_time - current_time)
        if delta < (1 / 100):
            time.sleep((1 / 100) - delta)
        next_time = time.time()
        delta = (next_time - current_time)
        if delta != 0:
            fps = 1 / delta
            count += 1
            total += fps
        avg_fps = (total / count)
        print(avg_fps)
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
    img = img.convert("L")
    return img


def check_text(target_text, img, dummy):
    global next_split, dupe_split, block_screenshots
    target_text = target_text.lower()
    api.SetImage(img)
    text = api.GetUTF8Text()
    # text = pytesseract.image_to_string(img, config=r"--psm 6 --oem 3", lang='eng')
    # for psm in range(6, 13 + 1):
    #     config = '--oem 3 --psm %d' % psm
    #     text = pytesseract.image_to_string(img, config=config, lang='eng')
    #     print('psm ', psm, ':', text)
    text = text.lower()
    print("TEXT: " + str(text))
    if target_text in text:
        # print("TRIGGER")
        if not dummy:
            pyautogui.press('num1')
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
    check_text("NEW", img, dummy)


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


# run_splits = [
#    # Darkness Zone
#    ("Respawning Restricted", False),
#    # First Totem done
#    ("Access Granted", False),
#    # second totem done
#    ("Access Granted", False),
#    # dummy for add clear start
#    ("New Objective", True),
#    # add clear done
#    ("New Objective", False),
#    # transition/hydra start
#    ("New Objective", False),
#    # hydra ded
#    ("New Objective", False),
#    # transition 2/brakion start
#    ("New Objective", False),
#    # p1 done
#    ("Brakion", False),
#    # p2 done
#    ("Brakion", False),
#    # brakion ded
#    ("MC", False)]

# start_auto_splitter(run_splits)
def get_main_monitor():
    for m in get_monitors():
        if m.is_primary:
            return m


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
