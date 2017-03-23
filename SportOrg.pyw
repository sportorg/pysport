from tkinter import Tk
import sys

from app import App


def main(argv):
    file = argv[2] if 2 in argv else None
    root = Tk()
    app = App(master=root, file=file)
    app.mainloop()


if __name__ == '__main__':
    main(sys.argv)
