import customtkinter
import autosplitter
from tkinter import filedialog as fd


def add_split(name, is_dummy):
    new_split = customtkinter.CTkTextbox(app, width=400, height=2, corner_radius=0)
    new_split.configure(state='normal')
    new_split.insert("0.0", name)

    if is_dummy:
        new_split.configure(fg_color="gray")

    new_split.configure(state='disabled')
    new_split.pack()
    run_splits.append((name, is_dummy))
    split_text_boxes.append(new_split)


def remove_split():
    if len(split_text_boxes) > 0:
        split_text_boxes[-1].pack_forget()
        del(split_text_boxes[-1])
        del(run_splits[-1])


def clear_splits():
    i = len(split_text_boxes)
    for j in range(i):
        remove_split()


def manual_add_split():
    command = split_option.get()
    is_dummy = dummy.get() == 1
    print(is_dummy)
    if command != "Custom":
        add_split(command, is_dummy)
    else:
        add_split(split_text.get("0.0", 'end-1c'), is_dummy)


def save_splits():
    dialog = customtkinter.CTkInputDialog(text="Save as:", title="Save")
    input_value = dialog.get_input()
    with open(input_value + '.txt', 'w') as f:
        for split in run_splits:
            f.write(split[0] + "," + str(split[1]) + "\n")


def load_splits():
    filetypes = (('text files', '*.txt'), ('All files', '*.*'))
    filename = fd.askopenfilename(title='Open a file', initialdir='/', filetypes=filetypes)
    print(filename)
    if filename != "":
        clear_splits()
        with open(filename, 'r') as f:
            for line in f:
                temp = line.split(",")
                if temp[1] == "True\n":
                    b = True
                else:
                    b = False
                run_splits.append((temp[0], b))
                add_split(temp[0], b)


def option_menu_callback(choice):
    if choice == "Custom":
        split_text.configure(state='normal', fg_color="#1D1E1E")
    else:
        # print(split_text._fg_color)
        split_text.delete("0.0", "end")
        split_text.configure(state='disabled', fg_color="gray")
    # print("optionmenu dropdown clicked:", choice)


run_splits = []
split_text_boxes = []

# setup UI
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
app.geometry("720x480")
app.title("Destiny 2 Autosplitter")

title = customtkinter.CTkLabel(app, text="Autosplitter :D")
title.pack(padx=10, pady=10)

start = customtkinter.CTkButton(app, text="Start Autosplitter",
                                command=lambda: autosplitter.start_auto_splitter(run_splits))
start.pack(pady=10, side=customtkinter.TOP)

stop = customtkinter.CTkButton(app, text="Stop Autosplitter", command=lambda: autosplitter.stop_auto_splitter())
stop.pack(pady=10, side=customtkinter.TOP)

save = customtkinter.CTkButton(app, text="Save Splits", command=lambda: save_splits())
save.pack(pady=10)

load = customtkinter.CTkButton(app, text="Load Splits", command=lambda: load_splits())
load.pack(pady=10)

split_option = customtkinter.CTkOptionMenu(app,  values=["New Objective", "Respawning Restricted", "Mission Completed",
                                                         "Custom"], command=option_menu_callback)
split_option.pack()

split_text = customtkinter.CTkTextbox(app, width=400, height=2, corner_radius=0)
split_text.pack(pady=10)

option_menu_callback(split_option.get())

add = customtkinter.CTkButton(app, text="Add Split", command=lambda: manual_add_split())
add.pack(pady=10)

add = customtkinter.CTkButton(app, text="Remove Last Split", command=lambda: remove_split())
add.pack(pady=10)

dummy = customtkinter.CTkCheckBox(app, text="dummy")
dummy.pack(pady=10)

app.mainloop()
