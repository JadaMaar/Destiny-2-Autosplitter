from datetime import datetime
import customtkinter
import time
import threading as th
import mss
from PIL import Image
import tesserocr
import numpy as np
import cv2
import livesplit
from customtkinter import ThemeManager
from screeninfo import get_monitors
import os
import sys

import gui


class Split:
    def __init__(self, name, split_name, dummy, spawn=None):
        self.name = name
        self.split_name = split_name
        self.dummy = dummy
        # only set for boss splits
        # set True for boss spawn and False for boss death split
        self.spawn = spawn
        split_to_text_map = {
            "New Objective": "NEW",
            "Objective Complete": "COMPLETE",
            "Respawning Restricted": "Respawning Restricted",
            "Mission Completed": "Mission",
            "Boss Spawn": None,
            "Boss Dead": None,
            "Wipe Screen": "YOUR",
            "Joining Allies": "joining"
        }
        if split_name in split_to_text_map:
            self.split_text = split_to_text_map[split_name]
        else:
            self.split_text = split_name

    def set_spawn(self, spawn):
        self.spawn = spawn


class AutoSplitter:
    def __init__(self, split_list: list[Split], split_ui: list[customtkinter.CTkTextbox]):
        self._split_list = split_list
        self._split_ui = split_ui
        self._split_index = 0
        self._is_running = False
        self._reset = False
        self._next_split = False
        self._block_screenshots = False
        self._dupe_split = False
        self._auto_split = False
        self._boss_dead_buffer = 3
        self._fps_cap = 100
        self._screen_checker = ScreenChecker()
        self._current_split = None
        self._livesplit = livesplit.Livesplit()

    def setup_livesplit_server(self):
        try:
            self._livesplit.getSocket()
            connected = True
        except:
            print("Connection failed. Please start the livesplit server")
            connected = False
            #time.sleep(1)
        if connected:
            th.Thread(target=self.get_hotkeys, daemon=True).start()
        return connected

    def start_auto_splitter(self):
        if len(self._split_list) > 0:
            split_thread = th.Thread(target=self._start_auto_splitter, daemon=True)
            split_thread.start()
            return True
        return False

    def stop_auto_splitter(self):
        self._is_running = False
        self._next_split = False
        self.update_split_ui()

    def _start_auto_splitter(self):
        self._screen_checker.init_sct()
        self._is_running = True
        count = 0
        total = 0
        self._split_index = 0
        self._next_split = False
        current_time = datetime.now().timestamp()
        while self._is_running:
            #####
            if self._reset:
                self._reset = False
                print("reset")
                break
            #####
            if not self._next_split:
                self._next_split = True

                # check if not last split
                if len(self._split_list) > self._split_index:
                    self._boss_dead_buffer = 3

                    # update current split
                    self._current_split = self._split_list[self._split_index]
                    self.update_split_ui()
                    print("CURRENT SPLIT: " + str(self._current_split.split_name))
                    self._split_index += 1

                    # check if the next split matches the current one to avoid double splitting
                    if len(self._split_list) > self._split_index:
                        self._dupe_split = self._current_split.split_name == self._split_list[self._split_index].split_name
                        print("NEXT SPLIT: " + str(self._split_list[self._split_index].split_name))
                    else:
                        self._dupe_split = False

            if not self._block_screenshots:
                split_triggered = self._screen_checker.take_screenshot(split=self._current_split)
                if split_triggered:
                    if self._current_split.split_name == "Boss Dead":
                        if self._boss_dead_buffer <= 0:
                            self.trigger_split()
                        else:
                            self._boss_dead_buffer -= 1
                    else:
                        self.trigger_split()
                else:
                    self._boss_dead_buffer = 3

                # cap frames
                next_time = datetime.now().timestamp()
                delta = (next_time - current_time)
                if delta < (1 / self._fps_cap):
                    time.sleep((1 / self._fps_cap) - delta)

                # calculate fps for debugging
                current_time = datetime.now().timestamp()
                if delta != 0:
                    fps = 1 / delta
                    count += 1
                    total += fps
                if count != 0:
                    avg_fps = (total / count)
                # print(avg_fps)
        if self._is_running:
            self.start_auto_splitter()

    def set_next_split(self):
        self._next_split = False
        self._block_screenshots = False

    def trigger_split(self):
        # split if not dummy
        if not self._current_split.dummy:
            self._livesplit.startOrSplit()
            self._auto_split = True
        # delay next split in case of dupe to prevent double splitting
        if self._dupe_split:
            self._block_screenshots = True
            th.Timer(6, self.set_next_split).start()
        else:
            self._next_split = False

    def update_split_ui(self):
        # TODO: change color in ui
        for i in range(len(self._split_list)):
            if self._split_list[i] == self._current_split and self._is_running:
                self._split_ui[i].configure(fg_color="green")
            else:
                if self._split_list[i].dummy:
                    self._split_ui[i].configure(fg_color="gray")
                else:
                    self._split_ui[i].configure(fg_color=ThemeManager.theme["CTkTextbox"]["fg_color"])

    def get_hotkeys(self):
        # TODO: kill thread after application is closed
        ls_socket = self._livesplit.getSocket()  # socket()
        prev_index = -1
        while True:
            try:
                ls_socket.send("getsplitindex\r\n".encode())
                current_index = int(ls_socket.recv(1024).decode()[:-2])
                # print(self._split_index)
                index_change = current_index != prev_index
                if not self._auto_split and index_change:
                    # index 0 or -1 meaning it just started or ended
                    if current_index <= 0:
                        print("RESET")
                        self._reset = True
                    elif current_index < prev_index:
                        print("MANUAL CHANGE")
                        self._split_index -= 2
                        print(current_index)
                        self._next_split = False
                    else:
                        while self._split_list[self._split_index].dummy:
                            self._split_index += 1
                        print(current_index)
                        self._next_split = False
                else:
                    self._auto_split = False
                if index_change:
                    prev_index = current_index
                time.sleep(0.1)
            except:
                print("timeout")
                gui.ServerErrorWindow(self.setup_livesplit_server).grab_set()
                return


class ScreenChecker:

    def __init__(self):
        # box that checks the content of the current prompt in the bottom left corner
        self._prompt_box = {"top": 825, "left": 40, "width": 370, "height": 35}
        # box that checks respawn restricted
        self._restricted_box = {"top": 460, "left": 840, "width": 240, "height": 30}
        # new objective box
        self._new_objective_box = {"top": 265, "left": 190, "width": 260, "height": 30}
        # new objective box
        self._objective_complete_box = {"top": 265, "left": 155, "width": 260, "height": 30}
        # mission complete box
        self._mission_complete_box = {"top": 70, "left": 190, "width": 660, "height": 70}
        # boss hp bar
        self._boss_hp_box = {"top": 976, "left": 645, "width": 620, "height": 2}
        self._boss_name_box = {"top": 987, "left": 645, "width": 620, "height": 25}
        # wipe screen
        self._light_fading_box = {"top": 100, "left": 400, "width": 200, "height": 70}
        # joining allies
        self._joining_allies_box = {"top": 815, "left": 805, "width": 140, "height": 28}
        self._split_to_box_map = {
            "New Objective": self._new_objective_box,
            "Objective Complete": self._objective_complete_box,
            "Respawning Restricted": self._restricted_box,
            "Mission Completed": self._mission_complete_box,
            "Boss Spawn": self._boss_hp_box,
            "Boss Dead": self._boss_hp_box,
            "Wipe Screen": self._light_fading_box,
            "Joining Allies": self._joining_allies_box
        }

        self.monitor_setup()
        self._sct = None
        self._api = tesserocr.PyTessBaseAPI(path=resource_path(""), lang="eng")

    def init_sct(self):
        self._sct = mss.mss()

    def monitor_setup(self):
        monitors = get_monitors()
        for monitor in monitors:
            if monitor.is_primary:
                main_monitor = monitor
                break

        width = main_monitor.width
        height = main_monitor.height
        x_modifier = width / 1920
        y_modifier = height / 1080

        # if not 1080p it will apply 1440p measurements
        if width != 1920 and height != 1080:
            print("1440P")
            # these boxes are simply upscaled on higher resolution
            enhance_list = [self._light_fading_box, self._restricted_box]
            for box in enhance_list:
                box["left"] = int(box["left"] * x_modifier)
                box["top"] = int(box["top"] * y_modifier)
                box["width"] = int(box["width"] * x_modifier)
                box["height"] = int(box["height"] * y_modifier)
            # new objective 1440p
            self._new_objective_box = {"top": 350, "left": 250, "width": 266, "height": 40}
            self._split_to_box_map["New Objective"] = self._new_objective_box
            # boss hp 1440p
            self._boss_hp_box = {"top": 1302, "left": 860, "width": 845, "height": 2}
            self._split_to_box_map["Boss Spawn"] = self._boss_hp_box
            self._split_to_box_map["Boss Dead"] = self._boss_hp_box
            # boss name 1440p
            self._boss_name_box = {"top": 1320, "left": 1000, "width": 620, "height": 25}
            # joining allies 1440p
            self._joining_allies_box = {"top": 1057, "left": 1078, "width": 186, "height": 37}
            self._split_to_box_map["Joining Allies"] = self._joining_allies_box
            # prompt 1440p
            self._prompt_box = {"top": 1100, "left": 80, "width": 493, "height": 46}
            # objective complete 1440p
            self._objective_complete_box = {"top": 345, "left": 205, "width": 350, "height": 45}
            self._split_to_box_map["Objective Completed"] = self._objective_complete_box
            # mission complete 1440p
            self._mission_complete_box = {"top": 100, "left": 255, "width": 880, "height": 93}
            self._split_to_box_map["Mission Completed"] = self._mission_complete_box

    def take_screenshot(self, split: Split):
        # select screenshot area based on split
        if split.split_name in self._split_to_box_map:
            area = self._split_to_box_map[split.split_name]
        else:
            area = self._prompt_box

        sct_img = self._sct.grab(area)
        # convert to PIL image
        img = Image.new("RGB", sct_img.size)
        pixels = zip(sct_img.raw[2::4], sct_img.raw[1::4], sct_img.raw[::4])
        img.putdata(list(pixels))

        if split.spawn is None:
            return self.check_text(split, img)
        else:
            return self.check_boss(split, img)

    def check_text(self, split: Split, img: Image):
        # tesserocr implementation
        self._api.SetImage(img)
        text = self._api.GetUTF8Text().lower()
        target = split.split_text.lower()
        if target in text:
            return True
        return False

    def check_boss(self, split: Split, img: Image):
        light_orange = (14, 155, 155)
        dark_orange = (25, 249, 255)
        img1 = np.array(img)
        # hsv_img = cv2.cvtColor(img1, cv2.COLOR_RGB2HSV)
        # Image.fromarray(hsv_img).save("hsv_boss.png")

        # slice image in 10 even pieces
        m = img1.shape[0] // 1
        n = img1.shape[1] // 10
        tiles = [img1[x:x + m, y:y + n] for x in range(0, img1.shape[0], m) for y in range(0, img1.shape[1], n)]

        # counts boss hp in increments of 10%
        counter = 0
        prev_ratio = 0
        all_ratio = []
        for tile in tiles:
            # filter only orange pixels from image
            hsv_img = cv2.cvtColor(tile, cv2.COLOR_RGB2HSV)
            mask = cv2.inRange(hsv_img, light_orange, dark_orange)
            result = cv2.bitwise_and(tile, tile, mask=mask)
            # calculate the black to orange ratio
            number_of_black_pix = np.sum(result == 0)
            other_pixel = np.sum(result != 0)
            ratio = number_of_black_pix / (number_of_black_pix + other_pixel)
            all_ratio.append(ratio)
            if ratio < 0.1:
                if prev_ratio >= 0.1:
                    break
                counter += 1
            prev_ratio = ratio
            # ratio = yellow / total
            # print(f"tile ratio: {ratio}")
            # Image.fromarray(tile).show()

        # if less than 20% of the pixel are black the boss is spawned and more than 99% he's basically dead
        # with boss_hp_box_whole full hp + immune = 24% and full hp + damageable = 48%
        # TODO: adjust value
        # print(f"counter: {counter}")
        if split.spawn:
            check = counter > 8
            if check:
                sct_img = self._sct.grab(self._boss_name_box)
                # convert to PIL image
                img = Image.new("RGB", sct_img.size)
                pixels = zip(sct_img.raw[2::4], sct_img.raw[1::4], sct_img.raw[::4])
                img.putdata(list(pixels))
                self._api.SetImage(img)
                text = self._api.GetUTF8Text().replace(" ", "")
                print(f"length: {len(text)}")
                # more than 5 letters make it more likely for it to be a boss name instead of random environment
                if len(text) < 5:
                    check = False

        else:
            check = counter < 1 and all_ratio[0] > 0.99
        return check


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
