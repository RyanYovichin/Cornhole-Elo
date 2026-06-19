#!/usr/bin/env python3
import sys
import csv
from elo import elo

from PyQt5 import QtWidgets, QtCore
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ──────────────────────────────────────────────
# Add-game dialog
# ──────────────────────────────────────────────
class AddGameDialog(QtWidgets.QDialog):
    def __init__(self, next_num, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add Game')
        self.setMinimumWidth(300)
        layout = QtWidgets.QFormLayout(self)

        self.game_num = QtWidgets.QSpinBox()
        self.game_num.setRange(1, 99999)
        self.game_num.setValue(next_num)
        layout.addRow('Game #:', self.game_num)

        self.p1 = QtWidgets.QLineEdit(); layout.addRow('Winner 1 (P1):', self.p1)
        self.p2 = QtWidgets.QLineEdit(); layout.addRow('Winner 2 (P2):', self.p2)
        self.p3 = QtWidgets.QLineEdit(); layout.addRow('Loser 1  (P3):', self.p3)
        self.p4 = QtWidgets.QLineEdit(); layout.addRow('Loser 2  (P4):', self.p4)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def values(self):
        return (self.game_num.value(),
                self.p1.text().strip(), self.p2.text().strip(),
                self.p3.text().strip(), self.p4.text().strip())


# ──────────────────────────────────────────────
# Matplotlib canvas  (single-player spotlight)
# ──────────────────────────────────────────────
class EloCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(tight_layout=True, facecolor='#1a1a2e')
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        self._history = {}
        self._players = []
        self._draw_empty('Search for a player above')

    def _draw_empty(self, msg='No data'):
        self.ax.clear()
        self.fig.set_facecolor('#1a1a2e')
        self.ax.set_facecolor('#16213e')
        self.ax.text(0.5, 0.5, msg, transform=self.ax.transAxes,
                     ha='center', va='center', fontsize=13,
                     color='#444466')
        self.ax.set_axis_off()
        self.draw()

    def set_data(self, history, players):
        self._history = history
        self._players = players

    def plot_player(self, player):
        if not player or not self._history:
            self._draw_empty('Compute Elo first')
            return
        # build series
        game_nums = sorted(self._history.keys())
        xs, ys = [], []
        for g in game_nums:
            val = self._history[g].get(player)
            if val is not None:
                xs.append(g)
                ys.append(val)
        if not xs:
            self._draw_empty(f'No data for "{player}"')
            return
        if xs[0] != -1:
            xs.insert(0, -1)
            ys.insert(0, 400)

        peak_val = max(ys)
        peak_idx = ys.index(peak_val)
        peak_x   = xs[peak_idx]
        curr_val = ys[-1]
        curr_x   = xs[-1]

        self.ax.clear()
        self.fig.set_facecolor('#1a1a2e')
        self.ax.set_facecolor('#0d1b2a')

        # dim baseline band
        self.ax.axhspan(100, peak_val*1.33333, color='#ffffff', alpha=0.03)
        self.ax.axhline(400, color='#ffffff', linewidth=0.8,
                        linestyle='--', alpha=0.3)

        # gradient-style fill: above baseline cyan all the way to 100, below pink all the way to 100
        self.ax.fill_between(xs, ys, 100,
                             where=[y >= 400 for y in ys],
                             color='#00b4d8', alpha=0.25, interpolate=True)
        self.ax.fill_between(xs, ys, 100,
                             where=[y < 400 for y in ys],
                             color='#e94560', alpha=0.25, interpolate=True)

        # main line
        self.ax.plot(xs, ys, color='#00b4d8', linewidth=2.8,
                     zorder=3, solid_capstyle='round')
        # regular dots
        self.ax.scatter(xs, ys, color='#00b4d8', s=30, zorder=4,
                        edgecolors='#1a1a2e', linewidths=0.8)

        # ── peak marker ──
        self.ax.scatter([peak_x], [peak_val], color='#f72585', s=120,
                        zorder=5, edgecolors='white', linewidths=1.2)
        self.ax.annotate(
            f'Peak\n{peak_val:.0f}',
            xy=(peak_x, peak_val),
            xytext=(0, 14), textcoords='offset points',
            ha='center', fontsize=9, fontweight='bold',
            color='#f72585',
            arrowprops=dict(arrowstyle='->', color='#f72585', lw=1.4))

        # ── current marker (only if different game from peak) ──
        if curr_x != peak_x:
            self.ax.scatter([curr_x], [curr_val], color='#90e0ef', s=120,
                            zorder=5, edgecolors='white', linewidths=1.2)
            self.ax.annotate(
                f'Now\n{curr_val:.0f}',
                xy=(curr_x, curr_val),
                xytext=(0, -22), textcoords='offset points',
                ha='center', fontsize=9, fontweight='bold',
                color='#90e0ef',
                arrowprops=dict(arrowstyle='->', color='#90e0ef', lw=1.4))

        for spine in self.ax.spines.values():
            spine.set_edgecolor('#2a2a4a')
        self.ax.tick_params(colors='#8888aa', labelsize=9)
        self.ax.set_xlabel('Game #', fontsize=10, color='#8888aa')
        self.ax.set_ylabel('Elo Rating', fontsize=10, color='#8888aa')
        self.ax.set_title(f'{player}  —  Elo over time',
                          fontsize=14, color='#ffffff',
                          fontweight='bold', pad=12)
        self.ax.grid(True, linestyle='--', linewidth=0.4,
                     alpha=0.25, color='#8888aa')
        self.draw()


# ──────────────────────────────────────────────
# Main window
# ──────────────────────────────────────────────
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Cornhole Elo')
        self.resize(950, 620)
        self.e = elo()

        tabs = QtWidgets.QTabWidget()
        tabs.setDocumentMode(True)
        self.setCentralWidget(tabs)

        # ── Games tab ──────────────────────────
        games_widget = QtWidgets.QWidget()
        g_layout = QtWidgets.QVBoxLayout(games_widget)

        bar = QtWidgets.QHBoxLayout()
        for label, slot in [('Load games.csv', self.load_games),
                             ('Add Game',       self.add_game),
                             ('Compute Elo',    self.compute_elo)]:
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(slot)
            bar.addWidget(btn)
        bar.addStretch()
        g_layout.addLayout(bar)

        self.games_table = QtWidgets.QTableWidget(0, 5)
        self.games_table.setHorizontalHeaderLabels(
            ['Game #', 'Winner 1', 'Winner 2', 'Loser 1', 'Loser 2'])
        self.games_table.horizontalHeader().setStretchLastSection(True)
        self.games_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.games_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.games_table.setSortingEnabled(True)
        self.games_table.setAlternatingRowColors(True)
        g_layout.addWidget(self.games_table)
        tabs.addTab(games_widget, 'Games')

        # ── Players tab ────────────────────────
        players_widget = QtWidgets.QWidget()
        p_layout = QtWidgets.QVBoxLayout(players_widget)

        exp_bar = QtWidgets.QHBoxLayout()
        export_btn = QtWidgets.QPushButton('Export players.csv')
        export_btn.clicked.connect(self.export_players)
        exp_bar.addWidget(export_btn)
        exp_bar.addStretch()
        p_layout.addLayout(exp_bar)

        self.players_table = QtWidgets.QTableWidget(0, 4)
        self.players_table.setHorizontalHeaderLabels(
            ['Rank', 'Player', 'Rating', 'Z-Score'])
        self.players_table.horizontalHeader().setStretchLastSection(True)
        self.players_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.players_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.players_table.setAlternatingRowColors(True)
        p_layout.addWidget(self.players_table)
        tabs.addTab(players_widget, 'Players')

        # ── Graph tab ──────────────────────────
        graph_widget = QtWidgets.QWidget()
        graph_layout = QtWidgets.QVBoxLayout(graph_widget)
        graph_layout.setContentsMargins(8, 8, 8, 4)

        search_bar = QtWidgets.QHBoxLayout()
        self.graph_search = QtWidgets.QLineEdit()
        self.graph_search.setPlaceholderText('Type a player name and press Enter…')
        self.graph_search.returnPressed.connect(self._search_player)
        search_bar.addWidget(self.graph_search)

        search_btn = QtWidgets.QPushButton('Show Graph')
        search_btn.clicked.connect(self._search_player)
        search_bar.addWidget(search_btn)
        graph_layout.addLayout(search_bar)

        self.canvas = EloCanvas()
        graph_layout.addWidget(self.canvas)
        tabs.addTab(graph_widget, 'Elo Graph')

        self.statusBar().showMessage('Ready — load games.csv to begin')

    # ── Slots ──────────────────────────────────
    def load_games(self):
        try:
            self.e.readgames()
            self._refresh_games()
            self.statusBar().showMessage(f'Loaded {len(self.e.games)} games')
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self, 'Missing', 'games.csv not found.')

    def _refresh_games(self):
        self.games_table.setSortingEnabled(False)
        self.games_table.setRowCount(0)
        for k in sorted(self.e.games):
            g = self.e.games[k]
            row = self.games_table.rowCount()
            self.games_table.insertRow(row)
            for col, val in enumerate([k,
                                       g['team1']['w1'], g['team1']['w2'],
                                       g['team2']['l1'], g['team2']['l2']]):
                self.games_table.setItem(row, col,
                                         QtWidgets.QTableWidgetItem(str(val)))
        self.games_table.setSortingEnabled(True)

    def add_game(self):
        next_num = max(self.e.games.keys(), default=0) + 1
        dlg = AddGameDialog(next_num, self)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        gnum, p1, p2, p3, p4 = dlg.values()
        if not all([p1, p2, p3, p4]):
            QtWidgets.QMessageBox.warning(self, 'Incomplete',
                                          'All 4 player names are required.')
            return
        with open('games.csv', 'a', newline='') as f:
            # store names normalized to lowercase for case-insensitive matching
            csv.writer(f).writerow([gnum, p1.lower(), p2.lower(), p3.lower(), p4.lower()])
        self.e.readgames()
        self._refresh_games()
        self.statusBar().showMessage(f'Game {gnum} added')

    def compute_elo(self):
        if not self.e.games:
            QtWidgets.QMessageBox.information(self, 'No games', 'Load games first.')
            return
        # Reset state and replay every game, capturing a rating snapshot after each
        self.e.players = {}
        self.e.zscore = {}
        history = {}
        game_nums = sorted(self.e.games)
        for game in game_nums:
            t1 = self.e.games[game]['team1']
            t2 = self.e.games[game]['team2']
            # seed any new players at base rating before this game runs
            for p in [t1['w1'], t1['w2'], t2['l1'], t2['l2']]:
                if p not in self.e.players:
                    # record their starting 400 at game-1 entry point
                    if -1 not in history:
                        history[-1] = {}
                    history[-1][p] = self.e.base
            self.e.gamescore(t1['w1'], t1['w2'], t2['l1'], t2['l2'])
            history[game] = dict(self.e.players)
        self._refresh_players()
        self.canvas.set_data(history, list(self.e.players.keys()))
        self.canvas._draw_empty('Search for a player above')
        self.statusBar().showMessage('Elo computed — go to Elo Graph and search a player')

    def _refresh_players(self):
        self.players_table.setRowCount(0)
        ranked = sorted(self.e.players.items(), key=lambda x: x[1], reverse=True)
        for rank, (player, rating) in enumerate(ranked, 1):
            row = self.players_table.rowCount()
            self.players_table.insertRow(row)
            z = self.e.zscore.get(player, '')
            for col, val in enumerate([rank, player, f'{rating:.2f}', z]):
                item = QtWidgets.QTableWidgetItem(str(val))
                if col != 1:
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.players_table.setItem(row, col, item)

    def _search_player(self):
        name = self.graph_search.text().strip()
        # case-insensitive match
        match = next((p for p in self.canvas._players
                      if p.lower() == name.lower()), None)
        if match:
            self.canvas.plot_player(match)
            self.statusBar().showMessage(f'Showing graph for {match}')
        else:
            self.canvas._draw_empty(f'Player "{name}" not found')
            self.statusBar().showMessage(f'No player found: {name}')

    def export_players(self):
        if not self.e.players:
            QtWidgets.QMessageBox.information(self, 'No data', 'Compute Elo first.')
            return
        with open('players.csv', 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['player', 'rating'])
            for p, r in self.e.players.items():
                w.writerow([p, r])
        self.statusBar().showMessage('players.csv exported')


# ──────────────────────────────────────────────
DARK_STYLE = """
/* ── base ── */
QWidget {
    background-color: #1a1a2e;
    color: #ccccdd;
    font-family: 'Segoe UI', sans-serif;
    font-size: 10pt;
}

/* ── tabs ── */
QTabWidget::pane {
    border: 1px solid #444466;
    background: #16213e;
}
QTabBar::tab {
    background: #0f3460;
    color: #ccccdd;
    padding: 7px 18px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #e94560;
    color: #ffffff;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background: #1a1a2e;
}

/* ── buttons ── */
QPushButton {
    background-color: #0f3460;
    color: #ccccdd;
    border: 1px solid #444466;
    border-radius: 5px;
    padding: 6px 14px;
}
QPushButton:hover {
    background-color: #e94560;
    color: #ffffff;
    border-color: #e94560;
}
QPushButton:pressed {
    background-color: #c0314a;
}

/* ── tables ── */
QTableWidget {
    background-color: #16213e;
    gridline-color: #2a2a4a;
    border: 1px solid #444466;
    border-radius: 4px;
    alternate-background-color: #1e2a4a;
    selection-background-color: #e94560;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #0f3460;
    color: #00b4d8;
    font-weight: bold;
    padding: 5px;
    border: none;
    border-bottom: 2px solid #e94560;
}

/* ── inputs ── */
QLineEdit, QSpinBox {
    background-color: #16213e;
    color: #ccccdd;
    border: 1px solid #444466;
    border-radius: 4px;
    padding: 4px 6px;
}
QLineEdit:focus, QSpinBox:focus {
    border-color: #00b4d8;
}
QSpinBox::up-button, QSpinBox::down-button {
    background: #0f3460;
    border: none;
    width: 16px;
}

/* ── dialog ── */
QDialog {
    background-color: #1a1a2e;
}
QDialogButtonBox QPushButton {
    min-width: 70px;
}

/* ── scrollbars ── */
QScrollBar:vertical, QScrollBar:horizontal {
    background: #1a1a2e;
    width: 8px;
    height: 8px;
    margin: 0;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #444466;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }

/* ── status bar ── */
QStatusBar {
    background: #0f3460;
    color: #00b4d8;
    font-size: 9pt;
    border-top: 1px solid #444466;
}

/* ── message box ── */
QMessageBox {
    background-color: #1a1a2e;
}
QMessageBox QLabel { color: #ccccdd; }
"""


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
