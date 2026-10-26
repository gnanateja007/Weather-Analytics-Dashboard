
import sys
from pathlib import Path

import pandas as pd
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QDateEdit,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class WeatherApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Palai Weather Analytics")
        self.resize(1100, 750)

        csv_path = Path(__file__).resolve().parent / "palai_weather.csv"

        try:
            self.df = pd.read_csv(csv_path)

            self.df["date"] = (
                pd.to_datetime(self.df["date"], utc=True)
                .dt.tz_convert("Asia/Kolkata")
                .dt.tz_localize(None)
            )

            if "temperature_2m" in self.df.columns:
                self.temp_col = "temperature_2m"
            else:
                self.temp_col = "temperature"

            self.df[self.temp_col] = pd.to_numeric(
                self.df[self.temp_col], errors="coerce"
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Cannot load CSV:\n{e}"
            )
            raise SystemExit(1)

        self.create_ui()
        self.update_weather()

    def create_card(self, title):
        label = QLabel(title + "\n--")
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("weatherCard")
        label.setMinimumHeight(100)
        return label

    def create_ui(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #101827;
                color: #ffffff;
                font-family: Segoe UI;
                font-size: 13px;
            }

            QLabel#heading {
                font-size: 28px;
                font-weight: bold;
                color: #6fc5ff;
            }

            QLabel#weatherCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 15px;
                font-size: 18px;
                font-weight: bold;
            }

            QPushButton {
                background-color: #0284c7;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #0369a1;
            }

            QDateEdit {
                background-color: #1e293b;
                border: 1px solid #475569;
                padding: 8px;
                border-radius: 5px;
            }

            QTableWidget {
                background-color: #1e293b;
                alternate-background-color: #263449;
                gridline-color: #334155;
            }

            QHeaderView::section {
                background-color: #334155;
                color: white;
                padding: 8px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)

        heading = QLabel("Palai Weather Analytics Dashboard")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        subtitle = QLabel(
            "Historical Temperature Analysis | CSV Dataset | Offline"
        )
        subtitle.setStyleSheet("color: #94a3b8;")
        layout.addWidget(subtitle)

        # Date selection
        controls = QHBoxLayout()

        controls.addWidget(QLabel("Select Date:"))

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd-MM-yyyy")

        first_date = self.df["date"].min()
        last_date = self.df["date"].max()

        self.date_input.setDate(
            QDate(first_date.year, first_date.month, first_date.day)
        )
        self.date_input.setDateRange(
            QDate(first_date.year, first_date.month, first_date.day),
            QDate(last_date.year, last_date.month, last_date.day)
        )

        controls.addWidget(self.date_input)

        button = QPushButton("Show Weather")
        button.clicked.connect(self.update_weather)

        controls.addWidget(button)
        controls.addStretch()

        layout.addLayout(controls)

        # Temperature summary
        cards = QHBoxLayout()

        self.avg_card = self.create_card("Average Temperature")
        self.max_card = self.create_card("Maximum Temperature")
        self.min_card = self.create_card("Minimum Temperature")

        cards.addWidget(self.avg_card)
        cards.addWidget(self.max_card)
        cards.addWidget(self.min_card)

        layout.addLayout(cards)

        # Matplotlib chart
        self.figure = Figure(figsize=(8, 3), facecolor="#1e293b")
        self.canvas = FigureCanvasQTAgg(self.figure)

        layout.addWidget(self.canvas, stretch=3)

        # Hourly weather table
        layout.addWidget(QLabel("Hourly Weather Records"))

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(
            ["Time (IST)", "Temperature (°C)"]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, stretch=2)

    def update_weather(self):
        selected_date = self.date_input.date().toPyDate()

        daily = self.df[
            self.df["date"].dt.date == selected_date
        ].sort_values("date")

        if daily.empty:
            QMessageBox.warning(
                self, "No Data", "No weather data for this date."
            )
            return

        temp = daily[self.temp_col].dropna()

        if temp.empty:
            QMessageBox.warning(
                self, "No Data", "No temperature readings available."
            )
            return

        self.avg_card.setText(
            f"Average Temperature\n{temp.mean():.2f} °C"
        )
        self.max_card.setText(
            f"Maximum Temperature\n{temp.max():.2f} °C"
        )
        self.min_card.setText(
            f"Minimum Temperature\n{temp.min():.2f} °C"
        )

        # Plot temperature
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#1e293b")

        ax.plot(
            daily["date"].dt.hour,
            daily[self.temp_col],
            color="#38bdf8",
            marker="o",
            linewidth=2,
            markersize=4
        )

        ax.set_title(
            f"Hourly Temperature - {selected_date}",
            color="white",
            fontsize=13
        )

        ax.set_xlabel("Hour (IST)", color="white")
        ax.set_ylabel("Temperature (°C)", color="white")

        ax.tick_params(colors="white")
        ax.grid(True, alpha=0.2)

        ax.set_xticks(range(0, 24, 2))

        for spine in ax.spines.values():
            spine.set_color("#64748b")

        self.figure.tight_layout()
        self.canvas.draw()

        # Update table
        self.table.setRowCount(len(daily))

        for row, (_, record) in enumerate(daily.iterrows()):
            time = record["date"].strftime("%H:%M")
            value = record[self.temp_col]

            self.table.setItem(
                row, 0, QTableWidgetItem(time)
            )

            temperature_text = (
                f"{value:.2f}" if pd.notna(value) else "N/A"
            )

            self.table.setItem(
                row, 1, QTableWidgetItem(temperature_text)
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = WeatherApp()
    window.show()

    sys.exit(app.exec_())
