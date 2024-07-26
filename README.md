![Screenshot 2024-07-26 122128](https://github.com/user-attachments/assets/1d58353e-fe91-4870-85fd-748c0bf69b94)

# Simple Hard Drive Defragmenter

## Overview

The Simple Hard Drive Defragmenter is a Python-based tool designed to optimize and defragment hard drives. This tool offers various defragmentation modes, customizable settings, and a user-friendly dark mode GUI built with PyQt5. 

## Features

- **Multiple Defragmentation Modes**: Quick Defrag, Full Defrag, Consolidation, Free Space Consolidation, Folder/File Name, Recency, Volatility.
- **Progress Tracking**: Real-time progress bar to monitor the defragmentation process.
- **Pause and Resume**: Easily pause and resume the defragmentation process.
- **Cancel Operation**: Cancel the defragmentation process at any time.
- **Detailed Logging**: Logs actions with timestamps to a file.
- **User Notifications**: Popup messages for important events.
- **Customizable Settings**: Options for block size and defragmentation speed.
- **Dark Mode**: User-friendly dark mode interface.
- **Disk Analysis Report**: Logs the start and completion of the defragmentation process.

## Prerequisites

- Python 3.x
- PyQt5

## Logging

Logs are saved to `defragmentation.log` in the following format:

```plaintext
2023-07-26 10:00:00 - INFO - Starting defragmentation on drive C...
2023-07-26 10:01:00 - INFO - Moved a fragmented block to a new position.
2023-07-26 10:02:00 - INFO - Defragmentation completed.