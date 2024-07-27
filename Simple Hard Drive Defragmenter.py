import subprocess
import sys
import random
import time
import logging
import shutil
import tempfile
import mmap
import secrets
import os
import timeit
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
                             QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
                             QTextEdit, QProgressBar, QComboBox, QMessageBox)
from PyQt5.QtGui import QColor, QBrush, QFont
from PyQt5.QtCore import Qt, QTimer

def install_packages():
    required_packages = ['PyQt5']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

install_packages()

# Set up logging
logging.basicConfig(filename='defragmentation.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class Process:
    def __init__(self, name, start_location, file_size):
        self.name = name
        self.start_location = start_location
        self.file_size = file_size

class DefragmenterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.hard_drive = list('ABBB DXX EFG HHJJ   JKKJLLL MM PPM PP R  ')
        self.process_info = []
        self.is_paused = False
        self.is_canceled = False
        self.defrag_mode = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_defragmentation)
        self.current_job = None
        self.current_job_flags = 0
        self.abort_flag = False
        self.progress_line_length = 0

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
                 "Folder/File Name", "Recency", "Volatility", "Wipe Free Space"]
        hbox_modes = QHBoxLayout()
        for mode in modes:
            button = QPushButton(mode, self)
            button.setStyleSheet("background-color: red; color: #ffffff;")
            button.setCheckable(True)
            button.clicked.connect(self.toggle_mode)
            self.mode_buttons[mode] = button
            hbox_modes.addWidget(button)
        vbox.addLayout(hbox_modes)

        self.analyze_button = QPushButton("Analyze", self)
        self.analyze_button.setStyleSheet("background-color: #3c3f41; color: #ffffff;")
        self.analyze_button.clicked.connect(self.analyze_fragmentation)
        vbox.addWidget(self.analyze_button)

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

    def log(self, message, level="info"):
        colors = {"info": "#00ff00", "warning": "#ffff00", "error": "#ff0000"}
        self.log_output.setTextColor(QColor(colors.get(level, "#ffffff")))
        self.log_output.append(message)
        logging.log(getattr(logging, level.upper()), message)

    def toggle_mode(self):
        sender = self.sender()
        if sender.isChecked():
            sender.setStyleSheet("background-color: green; color: #ffffff;")
            self.defrag_mode = sender.text()
        else:
            sender.setStyleSheet("background-color: red; color: #ffffff;")
            self.defrag_mode = None

    def start_defragmentation(self):
        self.drive_letter = self.drive_entry.text().strip().upper()
        if not self.drive_letter or len(self.drive_letter) != 1:
            self.log("Invalid drive letter. Please enter a single letter (e.g., C).", "error")
            return

        if self.defrag_mode == "Wipe Free Space":
            self.log("Wiping free space...", "info")
            self.wipe_free_space()
            return

        self.log(f"Starting defragmentation on drive {self.drive_letter}...", "info")
        self.is_paused = False
        self.is_canceled = False
        self.progress_bar.setValue(0)
        self.initialize_blocks()
        self.analyze_hard_drive()
        self.timer.start(500)

    def pause_defragmentation(self):
        if not self.is_paused:
            self.is_paused = True
            self.timer.stop()
            self.log("Defragmentation paused.", "warning")

    def resume_defragmentation(self):
        if self.is_paused:
            self.is_paused = False
            self.timer.start(500)
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

        for i in range(len(self.hard_drive)):
            block = QGraphicsRectItem(0, 0, 20, 20)
            color = "green" if self.hard_drive[i] != ' ' else "red"
            block.setBrush(QBrush(QColor(color)))
            block.setPos(i % 10 * 22, i // 10 * 22)
            self.blocks.append(block)
            self.scene.addItem(block)

    def analyze_hard_drive(self):
        self.process_info = []
        free_space = 0

        for i, char in enumerate(self.hard_drive):
            if char == ' ':
                free_space += 1
            else:
                in_list = False
                for process in self.process_info:
                    if process.name == char:
                        process.file_size += 1
                        in_list = True
                        break
                if not in_list:
                    self.process_info.append(Process(char, i, 1))

        self.log(f"Analysis complete. Free space: {free_space}, Processes: {len(self.process_info)}", "info")

    def analyze_fragmentation(self):
        fragmented = 0
        contiguous = 0
        current_file = self.hard_drive[0]

        for i in range(1, len(self.hard_drive)):
            if self.hard_drive[i] != ' ':
                if self.hard_drive[i] == current_file:
                    contiguous += 1
                else:
                    fragmented += 1
                current_file = self.hard_drive[i]

        fragmentation_ratio = fragmented / (fragmented + contiguous) if (fragmented + contiguous) > 0 else 0
        self.log(f"Fragmentation Analysis: {fragmented} fragmented blocks, {contiguous} contiguous blocks. Fragmentation ratio: {fragmentation_ratio:.2%}", "info")

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
        empty_positions = [(i % 10 * 22, i // 10 * 22) for i in range(len(self.hard_drive)) if self.blocks[i].brush().color() == QColor("green")]

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
        progress = int(((len(self.hard_drive) - len(fragmented_blocks)) / len(self.hard_drive)) * 100)
        self.progress_bar.setValue(progress)

        # Simulate defragmentation by swapping blocks in the hard_drive list
        for process in self.process_info:
            if process.name != ' ':
                file_locations = [idx for idx, char in enumerate(self.hard_drive) if char == process.name]
                for idx in file_locations:
                    if self.hard_drive[idx] != process.name:
                        temp_char = self.hard_drive[idx]
                        self.hard_drive[idx] = self.hard_drive[process.start_location]
                        self.hard_drive[process.start_location] = temp_char
                        process.start_location += 1

    def wipe_free_space(self):
        chunksize = 1024 * 4096
        total, used, free = shutil.disk_usage(".")
        self.log(f"{free:,} bytes free space.", "info")
        try:
            iters = int(free / chunksize)
            leftover = free % chunksize
            self.log(f"Planning for {iters:,} blocks of {chunksize:,} bytes each + {leftover:,} final bytes.", "info")
            tmpdir = tempfile.mkdtemp(dir=".")
            begin = timeit.default_timer()
            for i in range(iters):
                starttime = timeit.default_timer()
                outfile, filename = tempfile.mkstemp(dir=tmpdir)
                mm = mmap.mmap(outfile, chunksize, access=mmap.ACCESS_WRITE)
                for j in range(chunksize):
                    mm[j] = 0
                mm.flush()
                for j in range(chunksize):
                    mm[j] = 255
                mm.flush()
                randoms = secrets.token_bytes(chunksize)
                for j in range(chunksize):
                    mm[j] = randoms[j]
                mm.flush()
                mm.close()
                os.close(outfile)
                time6 = timeit.default_timer()
                self.log(f"{i}/{iters} wrote {chunksize} bytes in {time6 - starttime:.2f} seconds ({int(chunksize / (time6 - starttime)):,} per second)", "info")
            if leftover > 0:
                outfile, filename = tempfile.mkstemp(dir=tmpdir)
                mm = mmap.mmap(outfile, leftover)
                randoms = secrets.token_bytes(leftover)
                for j in range(leftover):
                    mm[j] = randoms[j]
                mm.flush()
                mm.close()
                os.close(outfile)
                self.log(f"Wrote {leftover:,} bytes", "info")
        except KeyboardInterrupt:
            self.log("Interrupted", "warning")
            mm.flush()
            mm.close()
            os.close(outfile)
            sys.exit(1)
        except OSError as e:
            self.log(f"Got an OSError: {e}", "error")

        end = timeit.default_timer()
        elapsed = end - begin
        rate = int((iters * chunksize) / elapsed)
        total, used, free = shutil.disk_usage(".")
        self.log(f"{free:,} bytes free space.", "info")
        self.log(f"{elapsed:.3f} elapsed, {rate:,} per second", "info")

def main():
    app = QApplication(sys.argv)
    defragmenter = DefragmenterGUI()
    defragmenter.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
