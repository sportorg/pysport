from tkinter import Tk
import sys

from so_widget.app import App


def main(argv):
    try:
        file = argv[1]
    except IndexError:
        file = None
    root = Tk()
    app = App(master=root, file=file)
    app.mainloop()


if __name__ == '__main__':
    main(sys.argv)
