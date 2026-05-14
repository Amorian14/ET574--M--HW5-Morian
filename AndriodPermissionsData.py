import threading
import os

import wx
import wx.grid as gridlib

import pandas as pd
import numpy as np

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

SAMPLE_ROWS = 100



class ColumnPickerDialog(wx.Dialog):
    """Let the user pick which column holds the 0/1 class label."""

    def __init__(self, parent, columns):
        super().__init__(parent, title="Select Label Column", size=(370, 200))
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(
            wx.StaticText(
                self,
                label="No 'Result' column found.\n"
                      "Select the column containing class labels (0=benign, 1=malware):"
            ),
            0, wx.ALL, 10
        )

        self.choice = wx.Choice(self, choices=list(columns))
        self.choice.SetSelection(0)
        sizer.Add(self.choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        btn_sizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK)
        ok_btn.SetDefault()
        btn_sizer.AddButton(ok_btn)
        btn_sizer.AddButton(wx.Button(self, wx.ID_CANCEL))
        btn_sizer.Realize()
        sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 10)

        self.SetSizer(sizer)

    def get_selected_column(self):
        return self.choice.GetString(self.choice.GetSelection())


class MainFrame(wx.Frame):

    def __init__(self):
        super().__init__(
            parent=None,
            title="Android Permission Visualizer",
            size=(1400, 860)
        )

        self.df          = None   
        self.result_col  = "Result"
        self.top_n       = 10
        self._busy       = False
        self._col_filter = ""    
        panel     = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)



        tb = wx.BoxSizer(wx.HORIZONTAL)

        self.load_btn = wx.Button(panel, label="Load CSV")
        self.load_btn.Bind(wx.EVT_BUTTON, self.on_load_csv)

        self.graph_btn = wx.Button(panel, label="Generate Graphs")
        self.graph_btn.Bind(wx.EVT_BUTTON, self.on_generate_graphs)
        self.graph_btn.Disable()

        self.export_btn = wx.Button(panel, label="Export Graphs...")
        self.export_btn.Bind(wx.EVT_BUTTON, self.export_graphs)
        self.export_btn.Disable()


        tb.Add(wx.StaticText(panel, label="  Top N:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
        self.top_n_choice = wx.Choice(
            panel,
            choices=["5", "10", "15", "20", "25", "30"],
            size=(70, -1)
        )
        self.top_n_choice.SetStringSelection("10")
        self.top_n_choice.Bind(wx.EVT_CHOICE, self.on_top_n_change)


        self.col_search = wx.SearchCtrl(panel, size=(220, -1))
        self.col_search.SetDescriptiveText("Filter columns...")
        self.col_search.ShowCancelButton(True)
        self.col_search.Bind(wx.EVT_SEARCH,        self.on_col_filter)
        self.col_search.Bind(wx.EVT_SEARCH_CANCEL, self.on_col_filter_cancel)
        self.col_search.Bind(wx.EVT_TEXT,          self.on_col_filter)


        self.gauge = wx.Gauge(panel, range=100, size=(140, 16),
                              style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)
        self.gauge.Hide()

        for widget in (
            self.load_btn, self.graph_btn, self.export_btn,
            self.top_n_choice,
            wx.StaticText(panel, label="  Filter columns:"),
            self.col_search,
            self.gauge,
        ):
            tb.Add(widget, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        main_sizer.Add(tb, 0, wx.LEFT | wx.TOP, 4)
