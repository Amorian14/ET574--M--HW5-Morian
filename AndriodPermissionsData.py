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

self.notebook = wx.Notebook(panel)

    
        self.data_tab  = wx.Panel(self.notebook)
        data_sizer     = wx.BoxSizer(wx.VERTICAL)
        self.grid      = gridlib.Grid(self.data_tab)
        self.grid.CreateGrid(1, 1)
        self.grid.EnableEditing(False)
        data_sizer.Add(self.grid, 1, wx.EXPAND | wx.ALL, 5)
        self.data_tab.SetSizer(data_sizer)


        self.summary_tab  = wx.Panel(self.notebook)
        summary_sizer     = wx.BoxSizer(wx.VERTICAL)
        self.summary_text = wx.TextCtrl(
            self.summary_tab,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.HSCROLL
        )
        self.summary_text.SetFont(
            wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        )
        summary_sizer.Add(self.summary_text, 1, wx.EXPAND | wx.ALL, 5)
        self.summary_tab.SetSizer(summary_sizer)


        self.malware_tab, self.malware_fig, self.malware_canvas = self._make_graph_tab()
        self.benign_tab,  self.benign_fig,  self.benign_canvas  = self._make_graph_tab()
        self.compare_tab, self.compare_fig, self.compare_canvas = self._make_graph_tab()

        self.notebook.AddPage(self.data_tab,    "Dataset (sample)")
        self.notebook.AddPage(self.summary_tab, "Summary")
        self.notebook.AddPage(self.malware_tab, "Malware")
        self.notebook.AddPage(self.benign_tab,  "Benign")
        self.notebook.AddPage(self.compare_tab, "Comparison")

        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)


        self.status = self.CreateStatusBar(2)
        self.status.SetStatusWidths([-1, 260])
        self.SetStatusText("No file loaded.", 0)

        panel.SetSizer(main_sizer)
        self.Centre()
        self.Show()

def _make_graph_tab(self):
        tab    = wx.Panel(self.notebook)
        fig    = Figure(figsize=(8, 6))
        canvas = FigureCanvas(tab, -1, fig)
        sizer  = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(canvas, 1, wx.EXPAND)
        tab.SetSizer(sizer)
        return tab, fig, canvas

    def _set_busy(self, busy, status_msg=""):
        self._busy = busy
        self.load_btn.Enable(not busy)
        self.graph_btn.Enable(not busy and self.df is not None)
        self.export_btn.Enable(not busy and self._graphs_ready())
        if busy:
            self.gauge.Show()
            self.gauge.Pulse()
            self.SetStatusText(status_msg, 0)
        else:
            self.gauge.Hide()
            self.gauge.SetValue(0)
        self.Layout()

    def _graphs_ready(self):
        return getattr(self, "_graphs_generated", False)

    def shorten_permission(self, name):
        for prefix in [
            "android.permission.",
            "android.hardware.",
            "android.intent.action.",
            "com.android.launcher.permission.",
            "com.android.",
            "com.google.android.",
            "com.google.",
        ]:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        return name if len(name) <= 40 else name[:37] + "..."

 def on_load_csv(self, event):
        if self._busy:
            return
        with wx.FileDialog(
            self, "Open CSV File",
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
            path = dlg.GetPath()

        self._set_busy(True, "Reading {}...".format(os.path.basename(path)))
        threading.Thread(target=self._bg_read_csv, args=(path,), daemon=True).start()

    def _bg_read_csv(self, path):
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            wx.CallAfter(self._on_load_error, "Failed to read CSV:\n{}".format(exc))
            return
        if df.empty:
            wx.CallAfter(self._on_load_error, "The CSV file is empty.")
            return
        wx.CallAfter(self._resolve_label_column, df, path)

    def _resolve_label_column(self, df, path):
        if "Result" in df.columns:
            result_col = "Result"
        else:
            with ColumnPickerDialog(self, df.columns) as picker:
                if picker.ShowModal() == wx.ID_CANCEL:
                    self._set_busy(False)
                    self.SetStatusText("Load cancelled.", 0)
                    return
                result_col = picker.get_selected_column()

        unique_vals = df[result_col].dropna().unique()
        if not set(unique_vals).issubset({0, 1}):
            self._on_load_error(
                "Column '{}' must contain only 0 and 1.\nFound: {}".format(
                    result_col, sorted(unique_vals)[:10]
                )
            )
            return

        self.result_col  = result_col
        self._col_filter = ""
        self._set_busy(True, "Building sample table...")
        threading.Thread(
            target=self._bg_build_grid, args=(df, path), daemon=True
        ).start()

    def _bg_build_grid(self, df, path):
        """Background: take a sample, apply any column filter, stringify, build summary."""
        sample      = df.head(SAMPLE_ROWS)
        col_labels, cell_data = self._filter_and_stringify(sample, self._col_filter)
        summary     = self._build_summary_text(df)
        wx.CallAfter(self._on_grid_ready, df, path, col_labels, cell_data, summary)

    def _filter_and_stringify(self, sample_df, col_query):
        """Return (col_labels, cell_data) after applying the column name filter."""
        if col_query:
            q = col_query.lower()
            cols = [c for c in sample_df.columns if q in c.lower()]
        else:
            cols = list(sample_df.columns)

        col_labels = cols
        cell_data  = [
            [str(sample_df.iat[r, sample_df.columns.get_loc(c)]) for c in cols]
            for r in range(len(sample_df))
        ]
        return col_labels, cell_data

    def _on_grid_ready(self, df, path, col_labels, cell_data, summary):
        """Main thread: write sample into the grid."""
        self._write_grid(col_labels, cell_data)

        self.df = df
        self.col_search.SetValue("")
        self._col_filter = ""
        self.summary_text.SetValue(summary)
        self._graphs_generated = False

        total_rows = len(df)
        shown_rows = len(cell_data)
        total_cols = len(df.columns)
        fname = os.path.basename(path)

        self.SetStatusText("Loaded: {}".format(fname), 0)
        self.SetStatusText(
            "Showing {} of {} rows, {} cols".format(shown_rows, total_rows, total_cols), 1
        )
        self._set_busy(False)

    def _write_grid(self, col_labels, cell_data):
        """Write a col_labels / cell_data pair into the wx.Grid (main thread only)."""
        rows = len(cell_data)
        cols = len(col_labels)

        self.grid.BeginBatch()
        try:
            if self.grid.GetNumberRows() > 0:
                self.grid.DeleteRows(0, self.grid.GetNumberRows())
            if self.grid.GetNumberCols() > 0:
                self.grid.DeleteCols(0, self.grid.GetNumberCols())
            if rows:
                self.grid.AppendRows(rows)
            if cols:
                self.grid.AppendCols(cols)
            for c, label in enumerate(col_labels):
                self.grid.SetColLabelValue(c, label)
            for r, row_vals in enumerate(cell_data):
                for c, val in enumerate(row_vals):
                    self.grid.SetCellValue(r, c, val)
            self.grid.AutoSizeColumns()
        finally:
            self.grid.EndBatch()

    def _on_load_error(self, msg):
        self._set_busy(False)
        wx.MessageBox(msg, "Error", wx.OK | wx.ICON_ERROR)
