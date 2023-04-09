import time
import mss
import pyautogui
from PIL import Image
from pynput.keyboard import Controller
from pytesseract import pytesseract

sct = mss.mss()

# box that checks the content of the current prompt in the bottom left corner
prompt_box = {"top": 830, "left": 40, "width": 170, "height": 30}

# box that checks respawn restricted
restricted_box = {"top": 460, "left": 840, "width": 240, "height": 30}

# new objective box
new_objective_box = {"top": 265, "left": 190, "width": 200, "height": 30}

# mission complete box
mission_complete_box = {"top": 70, "left": 190, "width": 660, "height": 70}

# pytesseract installation path
path_to_tesseract = r"G:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.tesseract_cmd = path_to_tesseract

keyboard = Controller()

is_running = False
next_split = False


def start_auto_splitter(splits):
    global is_running, next_split
    is_running = True
    current_split = ""
    while is_running:
        if not next_split:
            next_split = True
            if len(splits) > 0:
                current_split = splits.pop(0)
            else:
                break

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


def stop_auto_splitter():
    global is_running
    is_running = False


def take_screenshot(area):
    sct_img = sct.grab(area)
    img = Image.new("RGB", sct_img.size)
    pixels = zip(sct_img.raw[2::4], sct_img.raw[1::4], sct_img.raw[::4])
    img.putdata(list(pixels))
    return img


def check_text(target_text, img, dummy):
    global next_split
    text = pytesseract.image_to_string(img, config=r"--psm 6 --oem 3")
    print(text)
    if target_text in text:
        # keyboard.press(KeyCode.from_vk(0x61))
        if not dummy:
            pyautogui.press('num1')
        time.sleep(6)
        next_split = False
        # break


def check_new_objective(dummy):
    img = take_screenshot(new_objective_box)
    check_text("NEW OBJECTIVE", img, dummy)


def check_darkness_zone(dummy):
    img = take_screenshot(restricted_box)
    check_text("Respawning Restricted", img, dummy)


def check_mission_complete(dummy):
    img = take_screenshot(mission_complete_box)
    check_text("MISSION COMPLETE", img, dummy)


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
