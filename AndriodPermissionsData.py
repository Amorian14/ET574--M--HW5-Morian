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

def on_col_filter(self, event):
        if self.df is None or self._busy:
            return
        query = self.col_search.GetValue().strip()
        if query == self._col_filter:
            return                          # no change
        self._col_filter = query
        self._set_busy(True, "Filtering columns...")
        sample = self.df.head(SAMPLE_ROWS)
        threading.Thread(
            target=self._bg_col_filter, args=(sample, query), daemon=True
        ).start()

    def _bg_col_filter(self, sample, query):
        col_labels, cell_data = self._filter_and_stringify(sample, query)
        wx.CallAfter(self._apply_col_filter, col_labels, cell_data, query)

    def _apply_col_filter(self, col_labels, cell_data, query):
        self._write_grid(col_labels, cell_data)
        total_cols   = len(self.df.columns)
        visible_cols = len(col_labels)
        total_rows   = len(self.df)
        shown_rows   = len(cell_data)
        if query:
            self.SetStatusText(
                "Showing {} of {} cols, {} of {} rows".format(
                    visible_cols, total_cols, shown_rows, total_rows
                ), 1
            )
        else:
            self.SetStatusText(
                "Showing {} of {} rows, {} cols".format(shown_rows, total_rows, total_cols), 1
            )
        self._set_busy(False)

    def on_col_filter_cancel(self, event):
        self.col_search.SetValue("")
        self.on_col_filter(event)
        
def _build_summary_text(self, df):
        total     = len(df)
        malware_n = int((df[self.result_col] == 1).sum())
        benign_n  = int((df[self.result_col] == 0).sum())

        perm_cols         = [c for c in df.columns if c != self.result_col]
        numeric_perm_cols = [c for c in perm_cols if pd.api.types.is_numeric_dtype(df[c])]

        lines = [
            "=" * 52,
            " DATASET SUMMARY",
            "=" * 52,
            "  Total samples       : {}".format(total),
            "  Malware  (label=1)  : {}  ({:.1f}%)".format(malware_n, malware_n / total * 100),
            "  Benign   (label=0)  : {}  ({:.1f}%)".format(benign_n,  benign_n  / total * 100),
            "  Total columns       : {}".format(len(df.columns)),
            "  Permission columns  : {}".format(len(perm_cols)),
            "  Numeric perm cols   : {}".format(len(numeric_perm_cols)),
            "  Dataset tab shows   : first {} rows".format(SAMPLE_ROWS),
            "",
        ]

        if numeric_perm_cols:
            perm_array  = df[numeric_perm_cols].to_numpy()
            used        = np.sum(perm_array, axis=0)
            used_count  = int(np.sum(used > 0))
            lines += [
                "  Permissions used >=1x: {} / {}".format(used_count, len(numeric_perm_cols)),
                "",
                "-" * 52,
                " TOP 10 MOST FREQUENT PERMISSIONS (ALL APPS)",
                "-" * 52,
            ]
            top10_idx = np.argsort(used)[-10:][::-1]
            for rank, i in enumerate(top10_idx, 1):
                short = self.shorten_permission(numeric_perm_cols[i])
                lines.append("  {:2}. {:<38} {}".format(rank, short, int(used[i])))

        return "\n".join(lines)

def on_top_n_change(self, event):
        self.top_n = int(self.top_n_choice.GetStringSelection())

def on_generate_graphs(self, event):
        if self.df is None or self._busy:
            return

        perm_cols = [
            c for c in self.df.columns
            if c != self.result_col and pd.api.types.is_numeric_dtype(self.df[c])
        ]
        if not perm_cols:
            wx.MessageBox("No numeric permission columns found.", "Error", wx.OK | wx.ICON_ERROR)
            return

        malware_df = self.df[self.df[self.result_col] == 1][perm_cols]
        benign_df  = self.df[self.df[self.result_col] == 0][perm_cols]

        if malware_df.empty or benign_df.empty:
            wx.MessageBox("Both malware and benign samples are required.", "Error", wx.OK | wx.ICON_ERROR)
            return

        self._set_busy(True, "Computing graph data...")
        threading.Thread(
            target=self._bg_compute_graphs,
            args=(malware_df, benign_df, np.array(perm_cols)),
            daemon=True
        ).start()

    def _bg_compute_graphs(self, malware_df, benign_df, permission_names):
        n             = min(self.top_n, len(permission_names))
        malware_array = malware_df.to_numpy()
        benign_array  = benign_df.to_numpy()
        n_mal         = len(malware_df)
        n_ben         = len(benign_df)

        mal_counts = np.sum(malware_array, axis=0)
        mal_idx    = np.argsort(mal_counts)[-n:]
        mal_names  = [self.shorten_permission(permission_names[i]) for i in mal_idx]
        mal_vals   = mal_counts[mal_idx].tolist()

        ben_counts = np.sum(benign_array, axis=0)
        ben_idx    = np.argsort(ben_counts)[-n:]
        ben_names  = [self.shorten_permission(permission_names[i]) for i in ben_idx]
        ben_vals   = ben_counts[ben_idx].tolist()

        difference = np.mean(malware_array, axis=0) - np.mean(benign_array, axis=0)
        cmp_idx    = np.argsort(difference)[-n:]
        cmp_names  = [self.shorten_permission(permission_names[i]) for i in cmp_idx]
        cmp_vals   = difference[cmp_idx].tolist()

        wx.CallAfter(self._on_graph_data_ready, dict(
            n=n, n_mal=n_mal, n_ben=n_ben,
            mal_names=mal_names, mal_vals=mal_vals,
            ben_names=ben_names, ben_vals=ben_vals,
            cmp_names=cmp_names, cmp_vals=cmp_vals,
        ))

    def _on_graph_data_ready(self, d):
        n, n_mal, n_ben = d["n"], d["n_mal"], d["n_ben"]

        self.malware_fig.clear()
        ax1 = self.malware_fig.add_subplot(111)
        bars = ax1.barh(d["mal_names"], d["mal_vals"], color="#d62728")
        ax1.bar_label(bars, fmt="%g", padding=3, fontsize=8)
        ax1.set_title("Top {} Most Common Malware Permissions  (n={})".format(n, n_mal), fontsize=11)
        ax1.set_xlabel("Frequency (# apps)")
        ax1.margins(x=0.12)
        self.malware_fig.tight_layout()
        self.malware_canvas.draw()

        self.benign_fig.clear()
        ax2 = self.benign_fig.add_subplot(111)
        bars2 = ax2.barh(d["ben_names"], d["ben_vals"], color="#2ca02c")
        ax2.bar_label(bars2, fmt="%g", padding=3, fontsize=8)
        ax2.set_title("Top {} Most Common Benign Permissions  (n={})".format(n, n_ben), fontsize=11)
        ax2.set_xlabel("Frequency (# apps)")
        ax2.margins(x=0.12)
        self.benign_fig.tight_layout()
        self.benign_canvas.draw()

        cmp_vals   = d["cmp_vals"]
        cmp_colors = ["#d62728" if v >= 0 else "#2ca02c" for v in cmp_vals]
        self.compare_fig.clear()
        ax3 = self.compare_fig.add_subplot(111)
        bars3 = ax3.barh(d["cmp_names"], cmp_vals, color=cmp_colors)
        ax3.bar_label(bars3, fmt="%.3f", padding=3, fontsize=8)
        ax3.axvline(0, color="black", linewidth=0.8, linestyle="--")
        ax3.set_title(
            "Top {} Permissions Most Indicative of Malware\n"
            "(prevalence difference: malware rate - benign rate)".format(n),
            fontsize=11
        )
        ax3.set_xlabel("Prevalence difference")
        ax3.margins(x=0.15)
        self.compare_fig.tight_layout()
        self.compare_canvas.draw()

        self._graphs_generated = True
        self._set_busy(False)
        self.SetStatusText("Graphs generated.", 0)
        self.notebook.SetSelection(2)


def export_graphs(self, event):
        with wx.DirDialog(
            self, "Choose export folder",
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
        ) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
            folder = dlg.GetPath()

        saved, errors = [], []
        for fig, fname in [
            (self.malware_fig, "malware_permissions.png"),
            (self.benign_fig,  "benign_permissions.png"),
            (self.compare_fig, "comparison_permissions.png"),
        ]:
            fpath = os.path.join(folder, fname)
            try:
                fig.savefig(fpath, dpi=150, bbox_inches="tight")
                saved.append(fname)
            except Exception as exc:
                errors.append("{}: {}".format(fname, exc))

        msg = "Saved {} file(s) to:\n{}".format(len(saved), folder)
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors)
        wx.MessageBox(msg, "Export complete", wx.OK | wx.ICON_INFORMATION)
