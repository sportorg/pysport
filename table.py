from tkinter import *
import tkinter.font as tkFont
import tkinter.ttk as ttk


class ListBox(Frame):
    """use a ttk.TreeView as a multicolumn ListBox"""

    def __init__(self, master=None, header=None, listbox=None):
        super().__init__(master)
        if header is None:
            header = []
        if listbox is None:
            listbox = []
        self.tree = None
        self.header = header
        self.list = listbox
        self._setup_widgets()
        self._build()

    def _setup_widgets(self):
        self.pack(fill='both', expand=True)
        # create a treeview with dual scrollbars
        self.tree = ttk.Treeview(columns=self.header, show="headings")
        vsb = ttk.Scrollbar(orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)
        self.tree.grid(column=0, row=0, sticky='nsew', in_=self)
        vsb.grid(column=1, row=0, sticky='ns', in_=self)
        hsb.grid(column=0, row=1, sticky='ew', in_=self)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _build(self):
        for col in self.header:
            self.tree.heading(col, text=col.title(),
                              command=lambda c=col: self.sort_by(c, 0))
            # adjust the column's width to the header string
            self.tree.column(col,
                             width=tkFont.Font().measure(col.title()))
        for item in self.list:
            self.tree.insert('', 'end', values=item)
            # adjust column's width if necessary to fit each value
            for ix, val in enumerate(item):
                col_w = tkFont.Font().measure(val)
                if self.tree.column(self.header[ix], width=None) < col_w:
                    self.tree.column(self.header[ix], width=col_w)

    def sort_by(self, col, descending):
        """sort tree contents when a column header is clicked on"""
        # grab values to sort
        data = [(self.tree.set(child, col), child)
                for child in self.tree.get_children('')]
        # if the data to be sorted is numeric change to float
        # data =  change_numeric(data)
        # now sort the data in place
        data.sort(reverse=descending)
        for ix, item in enumerate(data):
            self.tree.move(item[1], '', ix)
        # switch the heading so it will sort in the opposite direction
            self.tree.heading(col, command=lambda col=col: self.sort_by(col, int(not descending)))
