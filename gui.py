import customtkinter
from customtkinter import *
import threading as th


class ServerErrorWindow(customtkinter.CTkToplevel):
    def __init__(self, func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Error")
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._func = func

        self.label = customtkinter.CTkLabel(self, text="Connection failed. Please start the livesplit server")
        self.label.pack(padx=20, pady=20)

        self.exit = customtkinter.CTkButton(master=self,
                                            width=100,
                                            border_width=0,
                                            text='Exit',
                                            command=self._exit_event)
        self.exit.pack(padx=20, pady=20)
        th.Thread(target=self._check_connection, daemon=True).start()

    def _check_connection(self):
        connected = self._func()
        while not connected:
            connected = self._func()
        self.grab_release()
        self.destroy()

    def _exit_event(self):
        self.master.destroy()

    def _on_closing(self):
        if self._func():
            self.grab_release()
            self.destroy()


class DialogWindow(customtkinter.CTkInputDialog):
    def __init__(self, title: str = "CTkDialog", text: str = "CTkDialog"):
        super().__init__(title=title, text=text)

    def _create_widgets(self):

        self.grid_columnconfigure((0, 1), weight=1)
        self.rowconfigure(0, weight=1)

        self._label = CTkLabel(master=self,
                               width=300,
                               wraplength=300,
                               fg_color="transparent",
                               text_color=self._text_color,
                               text=self._text,)
        self._label.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

        self._entry = CTkEntry(master=self,
                               width=230,
                               fg_color=self._entry_fg_color,
                               border_color=self._entry_border_color,
                               text_color=self._entry_text_color)
        self._entry.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")

        self._ok_button = CTkButton(master=self,
                                    width=100,
                                    border_width=0,
                                    fg_color=self._button_fg_color,
                                    hover_color=self._button_hover_color,
                                    text_color=self._button_text_color,
                                    text='Ok',
                                    command=self._ok_event)
        self._ok_button.grid(row=2, column=0, columnspan=1, padx=(20, 10), pady=(0, 20), sticky="ew")

        self._cancel_button = CTkButton(master=self,
                                        width=100,
                                        border_width=0,
                                        fg_color=self._button_fg_color,
                                        hover_color=self._button_hover_color,
                                        text_color=self._button_text_color,
                                        text='Cancel',
                                        command=self._cancel_event)
        self._cancel_button.grid(row=2, column=1, columnspan=1, padx=(10, 20), pady=(0, 20), sticky="ew")

        self.after(150, lambda: self._entry.focus())  # set focus to entry with slight delay, otherwise it won't work
        self._entry.bind("<Return>", self._ok_event)
