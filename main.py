from tkinter import filedialog as fd
import customtkinter
import autosplitter
import os
import threading


def close():
    autosplitter.stop_auto_splitter()
    app.quit()
    app.destroy()


def add_split(name, is_dummy):
    stop_auto_splitter()
    new_split = customtkinter.CTkTextbox(split_container, width=400, height=2, corner_radius=0)
    new_split.configure(state='normal')
    new_split.insert("0.0", name)

    if is_dummy:
        new_split.configure(fg_color="gray")

    new_split.configure(state='disabled')
    new_split.pack()
    run_splits.append((name, is_dummy))
    split_text_boxes.append(new_split)


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
                add_split(temp[0], b)


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


if __name__ == "__main__":
    os.environ['OMP_THREAD_LIMIT'] = '1'

    run_splits = []
    split_text_boxes = []

    autosplitter.monitor_setup()

    # setup UI
    customtkinter.set_appearance_mode("Dark")
    customtkinter.set_default_color_theme("blue")

    app = customtkinter.CTk()
    app.geometry("400x550")
    app.title("Destiny 2 Autosplitter")
    # app.iconbitmap("WLZ.ico")
    app.resizable(False, False)

    title_label = customtkinter.CTkLabel(app, text="Autosplitter :D")
    title_label.grid(row=0, column=0, padx=10, pady=10, columnspan=2)

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
                                               values=["New Objective", "Respawning Restricted", "Mission Completed",
                                                       "Custom"], command=option_menu_callback)
    split_option.grid(row=3, column=0, columnspan=2)

    split_text = customtkinter.CTkTextbox(app, width=400, height=2, corner_radius=0)
    split_text.grid(row=4, column=0, pady=10, columnspan=2)

    option_menu_callback(split_option.get())

    add = customtkinter.CTkButton(app, text="Add Split", command=lambda: manual_add_split())
    add.grid(row=5, column=0, pady=10)

    remove = customtkinter.CTkButton(app, text="Remove Last Split", command=lambda: remove_split())
    remove.grid(row=5, column=1, pady=10)

    dummy = customtkinter.CTkCheckBox(app, text="dummy")
    dummy.grid(row=6, column=0, pady=10, columnspan=2)

    split_container = customtkinter.CTkScrollableFrame(app, width=200, height=200)
    split_container.grid(row=7, column=0, pady=10, columnspan=2)

    app.protocol("WM_DELETE_WINDOW", lambda: close())
    app.mainloop()
