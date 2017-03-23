from tkinter import Tk

from app import App
from model import *


def main():
    db.connect()
    db.create_tables([
        Event,
        Person,
        Extensions,
        ControlCard,
        CourseControl,
        Course,
        EventStatus,
        ResultStatus,
        Country,
        Contact,
        Address,
        PersonName,
        Start,
        SplitTime,
        Result
    ], safe=True)
    root = Tk()
    app = App(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
