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
