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
        self.pack(fill=BOTH, expand=True)
        # create a treeview with dual scrollbars
        self.tree = ttk.Treeview(columns=self.header, show="headings")
        vsb = ttk.Scrollbar(orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)
        self.tree.grid(column=0, row=0, sticky=NSEW, in_=self)
        vsb.grid(column=1, row=0, sticky=NS, in_=self)
        hsb.grid(column=0, row=1, sticky=EW, in_=self)
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
            self.tree.insert('', END, values=item)
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


class Table(ttk.Frame):
    """
    A read-only table using tkinter's TreeView class.
    The table has standard CRUD (Create, Update, Delete)
    functions as well as the ability to add common UI components
    such as y-scroll bars and popup menus.
    The Table class is built to behave similar to a standard tkinter
    widget and allows for table options to be set using the
    ``table['<option>']`` notation (e.g. ``table['ysb'] = True``)
    or using a configure function (e.g. ``table.configure(ysb=True)``).
    The following table options are supported:
    * ysb (Domain: True, False):  Y-Scroll Bar
    * popup (Domain: True, False): Popup Menu
    * max_rows (Domain:  +Integers):  Max Rows in table
    * padding (Domain:  +Integers):  Widget padding
    * height (Domain: +Integers):  Height of table in rows
    * column_widths (Domain: +Integers):  Table column widths
    :param master: Parent widget
    :param columns:  Columns of table
    :param kwargs:  Table options
    """

    def __init__(self, master, columns, **kwargs):

        super().__init__(master)
        self.columns = columns

        self._table_options = {
            'ysb': kwargs.get('ysb', False),
            'xsb': kwargs.get('xsb', False),
            'popup': kwargs.get('popup', False),
            'max_rows': kwargs.get('max_rows', 250),
            'padding': kwargs.get('padding', 0),
            'height': kwargs.get('height', 10),
            'column_widths': kwargs.get('column_widths', [200]*len(columns))
        }

        # GUI Components
        self._tree = ttk.Treeview(self)
        self._popup = Menu(self, tearoff=0)
        self._ysb = ttk.Scrollbar(self, orient=VERTICAL, command=self._tree.yview)
        self._xsb = ttk.Scrollbar(self, orient=HORIZONTAL, command=self._tree.xview)

        # Initial Widget Configuration
        self._initial_configuration()

    def create_row(self, row):
        """
        Inserts a row in the table.  The row parameter
        must be a Python dictionary or subclass which implements
        the same interface.  The keys of the dictionary are used to
        map each value to its corresponding column.  If the row
        parameter has additional keys not in the table's columns,
        the values are ignored and not inserted in the table.
        If the row parameter does not provide keys for each
        column in the table, values of None are inserted in the
        missing columns.
        :param row:  Row to be inserted in the table
        :type row: dict
        :return:  None
        """

        if not isinstance(row, dict):
            raise ValueError
        row = self._standardize_row(row)

        values = []
        for column in self.columns:
            value = row.get(column)
            values.append(value)
        self._tree.insert('', END, values=values)

    def update_row(self, update_info, **kwargs):
        """
        Update row(s) in table with new values.  The table
        will update all rows which map the keyword arguments
        provided in the function.  For example, consider the following
        table:
        ===     ===     ===
        a       b       c
        ===     ===     ===
        1       1       1
        2       2       2
        3       3       3
        ===     ===     ===
        The function call ``table.update_row({'b': 100}, a=2)`` would result
        in the new table:
        ===     ===     ===
        a       b       c
        ===     ===     ===
        1       1       1
        2       100     2
        3       3       3
        ===     ===     ===
        :param update_info:  Contains information to update row(s).
        :type update_info: dict
        :param kwargs: Column name keywords and values used to subset table
        :return:  None
        """

        if len(kwargs) < 1:
            raise KeyError('Keyword arguments must be provided to function')

        if not isinstance(update_info, dict):
            raise ValueError('Update info must be a dictionary')

        if not all(k in self.columns for k in kwargs):
            raise KeyError('Invalid key word arguments supplied to function')

        # Iterate through all rows in table
        for row in self._tree.get_children():

            row_dict = self._row_to_dict(row)
            # Check if column values match key word arguments
            if all(str(kwargs[key]) == row_dict[key] for key in kwargs):

                # Update row with new information
                for col, val in update_info.items():
                    self._tree.set(row, column=col, value=val)

    def delete_row(self, **kwargs):
        """
        Deletes all rows in table which match keyword arguments.
        This function behaves similar to ``update_row(.)``, but instead
        of updating values, it deletes the row which match
        the provided keyword arguments.
        :param kwargs: Column name keywords and values used to subset table
        :return: None
        """

        if len(kwargs) < 1:
            raise KeyError('Keyword arguments must be provided to function')

        if not all(k in self.columns for k in kwargs):
            raise KeyError('Invalid key word arguments supplied to function')

        # Iterate through all rows in table
        for row in self._tree.get_children():

            row_dict = self._row_to_dict(row)
            # Check if column values match key word arguments
            if all(str(kwargs[key]) == row_dict[key] for key in kwargs):
                self._tree.delete(row)

    def register_popup(self, label, command=None, accelerator=None):
        """
        Adds an item to the popup menu in the table.
        :param label:  Text to use in popup menu
        :param command:  Callback function to run on click
        :return: None
        """
        self._popup.add_command(label=label, command=command, accelerator=accelerator)

    def configure(self, **kwargs):
        """
        Configure table widget.  Allows user to set table options such as
        'height', 'ysb', 'popup', etc.   The function expects keywords which
        match table options.  This provides the same functionality as
        ``table['<table-option>'] = <value>``.
        :param kwargs:  Table option keywords and values.
        :return: None
        """

        for k, v in kwargs.items():
            self[k] = v

    def _configure_ysb(self):

        self._ysb.grid(row=0, column=1, sticky=NS)
        self._tree.configure(yscroll=self._ysb.set)
        if not self._table_options['ysb']:
            self._ysb.grid_forget()

    def _configure_popup(self):

        self._tree.bind('<Button-3>', self._display_popup)
        if not self._table_options['popup']:
            self._tree.bind('<Button-3>', None)

    def _configure_frame(self):

        super().configure(padding=self._table_options['padding'])

    def _configure_tree(self):
        self._tree.configure(height=self._table_options['height'])

    def _configure_columns(self):

        if len(self._table_options['column_widths']) != len(self.columns):
            raise ValueError('Invalid column_widths parameter')

        self._tree['show'] = 'headings'
        column_labels = tuple(column.title() for column in self.columns)
        self._tree['columns'] = self.columns

        for column_label, column, width in zip(column_labels, self.columns, self._table_options['column_widths']):
            self._tree.column(column, width=width, anchor=W, minwidth=10)
            self._tree.heading(column, text=column_label, command=lambda c=column: self.sort_by(c, 0))

    def _initial_configuration(self):

        self._tree.grid(column=0, row=0, sticky=NSEW, in_=self)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._configure_columns()
        self._configure_frame()
        self._configure_popup()
        self._configure_ysb()

    def _display_popup(self, event):

        try:
            self._popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            # Make sure to release the grab (Tk 8.0a1 only)
            self._popup.grab_release()

    def _standardize_row(self, row):

        normalized_row = {}
        for column in self.columns:
            if column in row:
                normalized_row[column] = row[column]
            else:
                normalized_row[column] = None
        return normalized_row

    def _row_to_dict(self, iid):
        values = self._tree.item(iid, 'values')
        row_dict = dict(zip(self.columns, values))
        return row_dict

    def __getitem__(self, key):
        return self._table_options[key]

    def __setitem__(self, key, value):

        if key in self._table_options.keys():
            self._table_options[key] = value

            if key == 'ysb':
                self._configure_ysb()
            elif key == 'popup':
                self._configure_popup()
            elif key == 'padding':
                self._configure_frame()
            elif key == 'column_widths':
                self._configure_columns()
            elif key == 'height':
                self._configure_tree()

        else:
            error_str = '%s is not a table option. Please choose from the following: -%s' % \
                        (key, ' -'.join(self._table_options))
            raise KeyError(error_str)

    def get_tree(self):
        return self._tree

    def is_numeric(self, s):
        """test if a string is numeric"""
        numeric = False
        for c in s:
            if c in "1234567890-.":
                numeric = True
        return numeric

    def change_numeric(self, data):
        """if the data to be sorted is numeric change to float"""
        new_data = []
        if self.is_numeric(data[0][0]):
            # change child to a float
            for child, col in data:
                new_data.append((float(child), col))
            return new_data
        return data

    def sort_by(self, col, descending):
        """sort tree contents when a column header is clicked on"""
        # grab values to sort
        data = [(self._tree.set(child, col), child) for child in self._tree.get_children('')]
        if data:
            # if the data to be sorted is numeric change to float
            data = self.change_numeric(data)
            # now sort the data in place
            data.sort(reverse=descending)
            for ix, item in enumerate(data):
                self._tree.move(item[1], '', ix)
            # switch the heading so that it will sort in the opposite direction
            self._tree.heading(col, command=lambda col=col: self.sort_by(col, int(not descending)))

    def bind_open(self, func=None, add=None):
        self._tree.bind("<<TreeviewOpen>>", func, add)

    def bind_select(self, func=None, add=None):
        self._tree.bind("<<TreeviewSelect>>", func, add)
