#!/usr/bin/env python
"""
VeloFrame Photo Frame Application - Main entry point
"""
import sys
from PySide6.QtWidgets import QApplication
from veloframe.viewer import PhotoFrame

def main():
    """Main entry point for the photo frame application."""
    app = QApplication(sys.argv)
    photo_frame = PhotoFrame()
    photo_frame.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
