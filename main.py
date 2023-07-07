import time
from tkinter import filedialog as fd
import customtkinter
import autosplitter
import threading
import psutil


def close():
    autosplitter.stop_auto_splitter()
    app.quit()
    app.destroy()


def add_split(name, split, is_dummy):
    stop_auto_splitter()

    new_split = autosplitter.Split(name, split, is_dummy)
    run_splits.append(new_split)

    new_split_ui = customtkinter.CTkTextbox(split_container, width=400, height=2, corner_radius=0)
    new_split_ui.configure(state='normal')
    if name != "" and name is not None:
        ui_text = f"{name} ({split})"
    else:
        ui_text = split
    new_split_ui.insert("0.0", ui_text)

    if is_dummy:
        new_split_ui.configure(fg_color="gray")

    new_split_ui.configure(state='disabled')
    new_split_ui.pack()
    split_text_boxes.append(new_split_ui)


def remove_split():
    stop_auto_splitter()
    if len(split_text_boxes) > 0:
        split_text_boxes[-1].pack_forget()
        del (split_text_boxes[-1])
        del (run_splits[-1])


def clear_splits():
    i = len(split_text_boxes)
    for j in range(i):
        remove_split()


def manual_add_split():
    command = split_option.get()
    is_dummy = dummy.get() == 1
    print(is_dummy)
    splitname = ""
    if name.get() == 1:
        dialog = customtkinter.CTkInputDialog(text="Splitname:", title="Set Splitname")
        splitname = dialog.get_input()
    if command != "Custom":
        add_split(splitname, command, is_dummy)
    else:
        add_split(splitname, split_text.get("0.0", 'end-1c'), is_dummy)


def save_splits():
    dialog = customtkinter.CTkInputDialog(text="Save as:", title="Save")
    input_value = dialog.get_input()
    # print(dialog._user_input)
    if input_value is not None:
        with open(input_value + '.txt', 'w') as f:
            for split in run_splits:
                f.write(f"{split.name},{split.split_name},{split.dummy}\n")


def load_splits():
    filetypes = (('text files', '*.txt'), ('All files', '*.*'))
    filename = fd.askopenfilename(title='Open a file', filetypes=filetypes)
    print(filename)
    if filename != "":
        clear_splits()
        with open(filename, 'r') as f:
            for line in f:
                temp = line.split(",")
                if temp[2] == "True\n":
                    b = True
                else:
                    b = False
                add_split(temp[0], temp[1], b)


def option_menu_callback(choice):
    if choice == "Custom":
        split_text.configure(state='normal', fg_color="#1D1E1E")
    else:
        # print(split_text._fg_color)
        split_text.delete("0.0", "end")
        split_text.configure(state='disabled', fg_color="gray")
    # print("optionmenu dropdown clicked:", choice)


def start_auto_splitter(splits):
    print(start.cget("fg_color"))
    autosplitter.start_auto_splitter_thread(splits)
    start.configure(fg_color="green")


def stop_auto_splitter():
    autosplitter.stop_auto_splitter()
    start.configure(fg_color="#1F6AA5")


def cap_fps():
    import cv2
    from PIL import Image
    import numpy as np
    # autosplitter.fps_cap = int(fps_cap.get("0.0", 'end-1c'))
    # time.sleep(1)
    # fps_cap_btn.configure(text=f"CAP FPS\nAVG {round(autosplitter.avg_fps, 2)} FPS")
    box = split_option.get()
    if box == "New Objective":
        autosplitter.take_screenshot(autosplitter.new_objective_box).show()
    if box == "Objective Complete":
        autosplitter.take_screenshot(autosplitter.objective_complete_box).show()
    if box == "Respawning Restricted":
        autosplitter.take_screenshot(autosplitter.restricted_box).show()
    if box == "Wipe Screen":
        autosplitter.take_screenshot(autosplitter.light_fading_box).show()
    if box == "Joining Allies":
        autosplitter.take_screenshot(autosplitter.joining_allies_box).show()
    if box == "Boss Spawn":
        img = autosplitter.take_screenshot(autosplitter.boss_hp_box)
        img = np.array(img)
        # im_bw = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY)[1]
        # img = Image.fromarray((im_bw))
        # img.show()
        # img.save("binary.png")
        # img = np.array(img)
        hsv_img = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        img = Image.fromarray(hsv_img)
        min_r = 255
        min_g = 255
        min_b = 255
        max_r = 0
        max_g = 0
        max_b = 0
        image = img.convert('RGBA')
        pixdata = img.load()
        for y in range(image.size[1]):
            for x in range(image.size[0]):
                if pixdata[x, y][0] < min_r:
                    min_r = pixdata[x, y][0]
                if pixdata[x, y][1] < min_g:
                    min_g = pixdata[x, y][1]
                if pixdata[x, y][2] < min_b:
                    min_b = pixdata[x, y][2]
                if pixdata[x, y][0] > max_r:
                    max_r = pixdata[x, y][0]
                if pixdata[x, y][1] > max_g:
                    max_g = pixdata[x, y][1]
                if pixdata[x, y][2] > max_b:
                    max_b = pixdata[x, y][2]
        print("min_r: " + str(min_r))
        print("min_g: " + str(min_g))
        print("min_b: " + str(min_b))
        print("max_r: " + str(max_r))
        print("max_g: " + str(max_g))
        print("max_b: " + str(max_b))

        # hsv_img.save("test.png")
    if box == "Mission Complete":
        autosplitter.take_screenshot(autosplitter.mission_complete_box).show()
    if box == "Custom":
        autosplitter.take_screenshot(autosplitter.prompt_box).show()


def screenshot():
    text = box_text.get("0.0", 'end-1c').split(";")
    top = int(text[0])
    left = int(text[1])
    width = int(text[2])
    height = int(text[3])
    autosplitter.take_screenshot({"top": top, "left": left, "width": width, "height": height}).show()


if __name__ == "__main__":
    import cv2
    from PIL import Image
    # os.environ['OMP_THREAD_LIMIT'] = '1'

    run_splits = []
    split_text_boxes = []

    autosplitter.monitor_setup()
    autosplitter.test()

    # setup UI
    customtkinter.set_appearance_mode("Dark")
    customtkinter.set_default_color_theme("blue")

    app = customtkinter.CTk()
    app.geometry("400x650")
    app.title("Destiny 2 Autosplitter")
    # app.iconbitmap("WLZ.ico")
    app.resizable(False, False)
    img = Image.open("test2.png")
    my_image = customtkinter.CTkImage(light_image=img,
                                      dark_image=img,
                                      size=(400, 650))
    bg = customtkinter.CTkLabel(app, image=my_image, text="")
    # bg.grid(row=0, column=0, columnspan=2, rowspan=9)

    # title_label = customtkinter.CTkLabel(app, text="Autosplitter :D")
    # title_label.grid(row=0, column=0, padx=10, pady=10, columnspan=2)
    fps_cap = customtkinter.CTkTextbox(app, width=150, height=2, corner_radius=0)
    fps_cap.grid(row=0, column=0, pady=10)

    fps_cap_btn = customtkinter.CTkButton(app, text="TEST", command=lambda: cap_fps())
    fps_cap_btn.grid(row=0, column=1, pady=10)

    start = customtkinter.CTkButton(app, text="Start Autosplitter",
                                    command=lambda: start_auto_splitter(run_splits.copy()))
    start.grid(row=1, column=0, pady=10)

    stop = customtkinter.CTkButton(app, text="Stop Autosplitter", command=lambda: stop_auto_splitter())
    stop.grid(row=1, column=1, pady=10)

    save = customtkinter.CTkButton(app, text="Save Splits", command=lambda: save_splits())
    save.grid(row=2, column=0, pady=10)

    load = customtkinter.CTkButton(app, text="Load Splits", command=lambda: load_splits())
    load.grid(row=2, column=1, pady=10)

    split_option = customtkinter.CTkOptionMenu(app,
                                               values=["New Objective", "Objective Complete", "Respawning Restricted",
                                                       "Wipe Screen", "Joining Allies",
                                                       "Boss Spawn", "Boss Dead", "Mission Completed", "Custom"],
                                               command=option_menu_callback)
    split_option.grid(row=3, column=0, columnspan=2)

    split_text = customtkinter.CTkTextbox(app, width=400, height=2, corner_radius=0)
    split_text.grid(row=4, column=0, pady=10, columnspan=2)

    option_menu_callback(split_option.get())

    add = customtkinter.CTkButton(app, text="Add Split", command=lambda: manual_add_split())
    add.grid(row=5, column=0, pady=10)

    remove = customtkinter.CTkButton(app, text="Remove Last Split", command=lambda: remove_split())
    remove.grid(row=5, column=1, pady=10)

    dummy = customtkinter.CTkCheckBox(app, text="dummy")
    dummy.grid(row=6, column=0, pady=10)

    name = customtkinter.CTkCheckBox(app, text="name")
    name.grid(row=6, column=1, pady=10)

    split_container = customtkinter.CTkScrollableFrame(app, width=200, height=200)
    split_container.grid(row=7, column=0, pady=10, columnspan=2)

    box_text = customtkinter.CTkTextbox(app, width=400, height=2, corner_radius=0)
    box_text.grid(row=8, column=0, pady=10, columnspan=2)

    screenshot_button = customtkinter.CTkButton(app, text="Screenshot", command=lambda: screenshot())
    screenshot_button.grid(row=9, column=0, pady=10, columnspan=2)

    app.protocol("WM_DELETE_WINDOW", lambda: close())
    app.mainloop()
