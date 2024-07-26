import subprocess
import sys
import random
import time
import logging
from datetime import datetime

def install_packages():
    required_packages = ['PyQt5']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

install_packages()

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsRectItem, 
                             QTextEdit, QProgressBar, QComboBox, QMessageBox)
from PyQt5.QtGui import QColor, QBrush, QFont
from PyQt5.QtCore import Qt, QRectF, QTimer

# Set up logging
logging.basicConfig(filename='defragmentation.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DefragmenterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Simple Hard Drive Defragmenter")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #2e2e2e; color: #ffffff;")

        vbox = QVBoxLayout()

        hbox_drive = QHBoxLayout()
        self.drive_label = QLabel("Enter Drive Letter (e.g., C):")
        self.drive_label.setStyleSheet("color: #ffffff;")
        hbox_drive.addWidget(self.drive_label)
        self.drive_entry = QLineEdit(self)
        self.drive_entry.setStyleSheet("background-color: #1e1e1e; color: #ffffff; border: 1px solid #3c3f41;")
        hbox_drive.addWidget(self.drive_entry)
        vbox.addLayout(hbox_drive)

        self.mode_buttons = {}
        modes = ["Quick Defrag", "Full Defrag", "Consolidation", "Free Space Consolidation",
                 "Folder/File Name", "Recency", "Volatility"]
        hbox_modes = QHBoxLayout()
        for mode in modes:
            button = QPushButton(mode, self)
            button.setStyleSheet("background-color: red; color: #ffffff;")
            button.setCheckable(True)
            button.clicked.connect(self.toggle_mode)
            self.mode_buttons[mode] = button
            hbox_modes.addWidget(button)
        vbox.addLayout(hbox_modes)

        self.defrag_button = QPushButton("Start Defragmentation", self)
        self.defrag_button.setStyleSheet("background-color: #3c3f41; color: #ffffff;")
        self.defrag_button.clicked.connect(self.start_defragmentation)
        vbox.addWidget(self.defrag_button)

        self.pause_button = QPushButton("Pause", self)
        self.pause_button.setStyleSheet("background-color: #3c3f41; color: #ffffff;")
        self.pause_button.clicked.connect(self.pause_defragmentation)
        vbox.addWidget(self.pause_button)

        self.resume_button = QPushButton("Resume", self)
        self.resume_button.setStyleSheet("background-color: #3c3f41; color: #ffffff;")
        self.resume_button.clicked.connect(self.resume_defragmentation)
        vbox.addWidget(self.resume_button)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setStyleSheet("background-color: #3c3f41; color: #ffffff;")
        self.cancel_button.clicked.connect(self.cancel_defragmentation)
        vbox.addWidget(self.cancel_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        vbox.addWidget(self.progress_bar)

        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setStyleSheet("background-color: #1e1e1e; border: 1px solid #3c3f41;")
        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)
        vbox.addWidget(self.graphics_view)

        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        vbox.addWidget(self.log_output)

        hbox_settings = QHBoxLayout()
        self.block_size_label = QLabel("Block Size:")
        self.block_size_label.setStyleSheet("color: #ffffff;")
        hbox_settings.addWidget(self.block_size_label)
        self.block_size_combo = QComboBox(self)
        self.block_size_combo.addItems(["Small", "Medium", "Large"])
        self.block_size_combo.setStyleSheet("background-color: #1e1e1e; color: #ffffff; border: 1px solid #3c3f41;")
        hbox_settings.addWidget(self.block_size_combo)

        self.speed_label = QLabel("Defrag Speed:")
        self.speed_label.setStyleSheet("color: #ffffff;")
        hbox_settings.addWidget(self.speed_label)
        self.speed_combo = QComboBox(self)
        self.speed_combo.addItems(["Slow", "Normal", "Fast"])
        self.speed_combo.setStyleSheet("background-color: #1e1e1e; color: #ffffff; border: 1px solid #3c3f41;")
        hbox_settings.addWidget(self.speed_combo)
        
        vbox.addLayout(hbox_settings)

        self.setLayout(vbox)

        self.blocks = []
        self.block_count = 100
        self.is_paused = False
        self.is_canceled = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_defragmentation)

    def log(self, message, level="info"):
        colors = {"info": "#00ff00", "warning": "#ffff00", "error": "#ff0000"}
        self.log_output.setTextColor(QColor(colors.get(level, "#ffffff")))
        self.log_output.append(message)
        logging.log(getattr(logging, level.upper()), message)

    def toggle_mode(self):
        sender = self.sender()
        if sender.isChecked():
            sender.setStyleSheet("background-color: green; color: #ffffff;")
        else:
            sender.setStyleSheet("background-color: red; color: #ffffff;")

    def start_defragmentation(self):
        self.drive_letter = self.drive_entry.text().strip().upper()
        if not self.drive_letter or len(self.drive_letter) != 1:
            self.log("Invalid drive letter. Please enter a single letter (e.g., C).", "error")
            return

        self.log(f"Starting defragmentation on drive {self.drive_letter}...", "info")
        self.is_paused = False
        self.is_canceled = False
        self.progress_bar.setValue(0)
        self.initialize_blocks()
        self.timer.start(100)

    def pause_defragmentation(self):
        if not self.is_paused:
            self.is_paused = True
            self.timer.stop()
            self.log("Defragmentation paused.", "warning")

    def resume_defragmentation(self):
        if self.is_paused:
            self.is_paused = False
            self.timer.start(100)
            self.log("Defragmentation resumed.", "info")

    def cancel_defragmentation(self):
        self.is_canceled = True
        self.timer.stop()
        self.log("Defragmentation canceled.", "warning")
        self.notify_user("Defragmentation process has been canceled.")

    def notify_user(self, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle("Notification")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def initialize_blocks(self):
        self.scene.clear()
        self.blocks = []

        for i in range(self.block_count):
            block = QGraphicsRectItem(0, 0, 20, 20)
            block.setBrush(QBrush(QColor("green" if random.random() > 0.7 else "red")))
            block.setPos(i % 10 * 22, i // 10 * 22)
            self.blocks.append(block)
            self.scene.addItem(block)

    def update_defragmentation(self):
        if self.is_canceled:
            self.timer.stop()
            return

        fragmented_blocks = [block for block in self.blocks if block.brush().color() == QColor("red")]
        if not fragmented_blocks:
            self.timer.stop()
            self.log("Defragmentation completed.", "info")
            self.notify_user("Defragmentation completed successfully.")
            return

        block_to_move = random.choice(fragmented_blocks)
        empty_positions = [(i % 10 * 22, i // 10 * 22) for i in range(self.block_count) if self.blocks[i].brush().color() == QColor("green")]

        if not empty_positions:
            self.timer.stop()
            self.log("No empty positions found. Defragmentation halted.", "warning")
            self.notify_user("Defragmentation halted due to lack of empty positions.")
            return

        new_position = random.choice(empty_positions)
        block_to_move.setPos(new_position[0], new_position[1])
        block_to_move.setBrush(QBrush(QColor("green")))
        self.log("Moved a fragmented block to a new position.", "info")

        # Update progress bar
        progress = ((self.block_count - len(fragmented_blocks)) / self.block_count) * 100
        self.progress_bar.setValue(progress)

def main():
    app = QApplication(sys.argv)
    defragmenter = DefragmenterGUI()
    defragmenter.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
