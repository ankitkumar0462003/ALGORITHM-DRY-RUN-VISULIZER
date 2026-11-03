# main.py - the entry point. Run it with:   python main.py

import tkinter as tk  # Tkinter creates the window

from gui import App  # the one class that builds and runs the whole interface


def main():
    root = tk.Tk()  # the main window
    App(root)  # build the interface inside it
    root.mainloop()  # keep the window open and react to clicks until it is closed


if __name__ == "__main__":  # only run when this file is started directly
    main()
