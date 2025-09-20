#!/usr/bin/env python3

import sys
import subprocess
import configparser
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, 
                           QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QIcon



class FloatingToolbar(QWidget):
    def __init__(self):
        super().__init__()
        self.config_file = "toolbar_config.ini"
        self.load_config()
        self.init_ui()
        
    def load_config(self):
        """Load configuration from INI file"""
        self.config = configparser.ConfigParser()
        
        # Create default config if it doesn't exist
        if not os.path.exists(self.config_file):
            self.create_default_config()
        
        self.config.read(self.config_file)
        
    def create_default_config(self):
        """Create default configuration file"""
        config = configparser.ConfigParser()
        config['Commands'] = {
            'rewind': 'echo "Rewind pressed"',
            'play': 'echo "Play pressed"',
            'pause': 'echo "Pause pressed"', 
            'stop': 'echo "Stop pressed"',
            'fast_forward': 'echo "Fast forward pressed"'
        }
        config['Appearance'] = {
            'button_size': '40',
            'window_opacity': '0.9',
            'stay_on_top': 'true',
            'initial_x': '100',
            'initial_y': '100'
        }
        
        with open(self.config_file, 'w') as f:
            config.write(f)
            
    def init_ui(self):
        """Initialize the user interface"""
        # Remove window decorations and make it frameless
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.Tool)
        
        # Set window properties
        self.setWindowTitle("Music Control Toolbar")
        
        # Set opacity if configured
        opacity = float(self.config.get('Appearance', 'window_opacity', fallback='0.9'))
        self.setWindowOpacity(opacity)
        
        # Create layout
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)  # Minimal margins
        layout.setSpacing(1)  # Minimal spacing between buttons
        
        # Button configuration
        button_size = int(self.config.get('Appearance', 'button_size', fallback='40'))
        buttons_config = [
            ('rewind', '⏮', 'Rewind'),
            ('play', '▶', 'Play'), 
            ('pause', '⏸', 'Pause'),
            ('stop', '⏹', 'Stop'),
            ('fast_forward', '⏭', 'Fast Forward')
        ]
        
        # Create buttons
        for cmd_key, symbol, tooltip in buttons_config:
            button = QPushButton(symbol)
            button.setFixedSize(QSize(button_size, button_size))
            button.setToolTip(tooltip)
            button.setStyleSheet("""
                QPushButton {
                    border: 1px solid #666;
                    border-radius: 4px;
                    background-color: #333;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #555;
                    border: 1px solid #888;
                }
                QPushButton:pressed {
                    background-color: #222;
                    border: 1px solid #999;
                }
            """)
            
            # Connect button to command
            button.clicked.connect(lambda checked, key=cmd_key: self.execute_command(key))
            
            # Enable dragging on buttons
            self.setup_dragging(button)
            
            layout.addWidget(button)
            
        self.setLayout(layout)
        
        # Size window to fit content
        self.adjustSize()
        self.setFixedSize(self.size())
        
        # Position window from config
        initial_x = int(self.config.get('Appearance', 'initial_x', fallback='100'))
        initial_y = int(self.config.get('Appearance', 'initial_y', fallback='100'))
        self.move(initial_x, initial_y)
        
        # Make window draggable
        self.draggable = False
        self.drag_started = False
        self.offset = None
        self.press_pos = None
        
    def execute_command(self, command_key):
        """Execute the command associated with the button"""
        try:
            command = self.config.get('Commands', command_key, fallback='')
            if command:
                # Execute command in background
                subprocess.Popen(command, shell=True)
            else:
                print(f"No command configured for {command_key}")
        except Exception as e:
            print(f"Error executing command for {command_key}: {e}")
            
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.draggable = True
            self.offset = event.position().toPoint()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.draggable and self.offset is not None:
            self.move(event.globalPosition().toPoint() - self.offset)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.draggable = False
            self.offset = None
            
    def setup_dragging(self, widget):
        """Enable dragging for a widget"""
        original_press = widget.mousePressEvent
        original_move = widget.mouseMoveEvent
        original_release = widget.mouseReleaseEvent
        
        def mouse_press(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.draggable = True
                self.drag_started = False  # Track if we actually started dragging
                self.offset = event.globalPosition().toPoint() - self.pos()
                self.press_pos = event.globalPosition().toPoint()
            # Always call original handler
            original_press(event)
            
        def mouse_move(event):
            if self.draggable and self.offset is not None:
                # Only start dragging if mouse moved more than a few pixels
                current_pos = event.globalPosition().toPoint()
                if not self.drag_started:
                    distance = (current_pos - self.press_pos).manhattanLength()
                    if distance > 5:  # 5 pixel threshold
                        self.drag_started = True
                
                if self.drag_started:
                    self.move(current_pos - self.offset)
                    return  # Don't call original move handler when dragging
            
            original_move(event)
            
        def mouse_release(event):
            if event.button() == Qt.MouseButton.LeftButton:
                was_dragging = self.drag_started
                self.draggable = False
                self.drag_started = False
                self.offset = None
                
                # Only call original handler if we weren't dragging
                if not was_dragging:
                    original_release(event)
            else:
                original_release(event)
        
        widget.mousePressEvent = mouse_press
        widget.mouseMoveEvent = mouse_move  
        widget.mouseReleaseEvent = mouse_release
            
    def contextMenuEvent(self, event):
        """Handle right-click to quit"""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtWidgets import QApplication
        menu = QMenu(self)
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        menu.exec(event.globalPos())

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setQuitOnLastWindowClosed(True)
    
    # Create and show toolbar
    toolbar = FloatingToolbar()
    toolbar.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
