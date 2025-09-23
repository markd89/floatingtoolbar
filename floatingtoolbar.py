#!/usr/bin/env python3

import sys
import subprocess
import configparser
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                           QPushButton, QSizePolicy, QComboBox, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QSettings, QSize, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QIcon

class FloatingToolbar(QWidget):
    def __init__(self):
        super().__init__()
        self.config_file = "toolbar_config.ini"
        self.expanded = False
        self.expanded_widget = None
        self.animation = None
        self.current_voice = None
        self.current_speed = None
        self.pending_voice = None  # Voice selected in dropdown but not applied yet
        self.pending_speed = None  # Speed selected in dropdown but not applied yet
        self.initializing = False
        self.init_label = None
        self.play_state = ""  # "", "playing", or "paused"
        self.load_config()
        self.init_ui()
        self.initialize_settings()
        
    def load_config(self):
        """Load configuration from INI file"""
        self.config = configparser.ConfigParser()
        
        # Create default config if it doesn't exist
        if not os.path.exists(self.config_file):
            self.create_default_config()
        
        self.config.read(self.config_file)
        
        # Load current settings
        self.current_voice = self.config.get('CurrentSettings', 'current_voice', fallback='')
        self.current_speed = self.config.get('CurrentSettings', 'current_speed', fallback='')
        
    def create_default_config(self):
        """Create default configuration file"""
        config = configparser.ConfigParser()
        config['Commands'] = {
            'record': 'echo "Record pressed"',
            'rewind': 'echo "Rewind pressed"',
            'play': 'echo "Play pressed"',
            'pause': 'echo "Pause pressed"',
            'resume': 'echo "Resume pressed"',
            'stop': 'echo "Stop pressed"',
            'fast_forward': 'echo "Fast forward pressed"'
        }
        config['VoiceSpeed'] = {
            'VoiceChoices': 'af_bella,af_nicole,af_heart,af_alloy,af_aoede,af_jessica,af_kore,af_nova,af_river,af_sarah,af_sky,am_adam,am_echo,am_eric,am_fenrir,am_liam,am_michael,am_onyx,am_puck,am_santa',
            'VoiceChange': 'echo "Voice changed to {choice}"',
            'SpeedChoices': '1.0,1.1,1.2,1.4,2.0,0.75',
            'SpeedChange': 'echo "Speed changed to {choice}"'
        }
        config['Appearance'] = {
            'button_size': '40',
            'window_opacity': '0.9',
            'stay_on_top': 'true',
            'initial_x': '100',
            'initial_y': '100',
            'animation': '1'
        }
        config['CurrentSettings'] = {
            'current_voice': '',
            'current_speed': ''
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
        
        # Create main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(0)
        
        # Create initialization label (hidden by default)
        self.init_label = QLabel("Initializing...")
        self.init_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.init_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: white;
                padding: 2px;
                font-size: 10px;
            }
        """)
        self.init_label.hide()
        self.main_layout.addWidget(self.init_label)
        
        # Create toolbar layout
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(1)
        
        # Button configuration - check if record command exists
        button_size = int(self.config.get('Appearance', 'button_size', fallback='40'))
        buttons_config = []
        
        # Add record button if configured
        if self.config.has_option('Commands', 'record'):
            buttons_config.append(('record', '⏺', 'Record'))
            
        # Add standard buttons
        buttons_config.extend([
            ('rewind', '⏮', 'Rewind'),
            ('play', '▶', 'Play'), 
            ('pause', '⏸', 'Pause'),
            ('stop', '⏹', 'Stop'),
            ('fast_forward', '⏭', 'Fast Forward')
        ])
        
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
            
            toolbar_layout.addWidget(button)
            
        # Create toolbar widget
        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar_layout)
        self.main_layout.addWidget(toolbar_widget)
        
        self.setLayout(self.main_layout)
        
        # Size window to fit content
        self.adjustSize()
        self.setFixedWidth(self.width())
        
        # Position window from config
        initial_x = int(self.config.get('Appearance', 'initial_x', fallback='100'))
        initial_y = int(self.config.get('Appearance', 'initial_y', fallback='100'))
        self.move(initial_x, initial_y)
        
        # Make window draggable
        self.draggable = False
        self.drag_started = False
        self.offset = None
        self.press_pos = None
        
        # Add keyboard shortcut for quit (Ctrl+Q)
        from PyQt6.QtGui import QShortcut, QKeySequence
        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.confirm_quit)
        
    def create_expanded_widget(self):
        """Create the expanded options widget"""
        expanded_widget = QWidget()
        expanded_widget.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 1px solid #666;
                border-top: none;
            }
            QLabel {
                color: white;
                font-weight: bold;
                padding: 5px;
            }
            QComboBox {
                background-color: #404040;
                color: white;
                border: 1px solid #666;
                padding: 5px;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                border: 2px solid #666;
                border-radius: 2px;
            }
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 50px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #222;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # Add margins: left, top, right, bottom
        layout.setSpacing(8)
        
        # Voice selection
        if self.config.has_section('VoiceSpeed') and self.config.has_option('VoiceSpeed', 'VoiceChoices'):
            voice_layout = QHBoxLayout()
            voice_label = QLabel("Voice:")
            voice_label.setFixedWidth(60)
            self.voice_combo = QComboBox()
            
            voice_choices = self.config.get('VoiceSpeed', 'VoiceChoices', fallback='').split(',')
            voice_choices = [choice.strip() for choice in voice_choices if choice.strip()]
            self.voice_combo.addItems(voice_choices)
            
            # Set current selection if available
            if self.current_voice and self.current_voice in voice_choices:
                self.voice_combo.setCurrentText(self.current_voice)
                self.pending_voice = self.current_voice
            
            self.voice_combo.currentTextChanged.connect(self.on_voice_dropdown_changed)
            
            voice_layout.addWidget(voice_label)
            voice_layout.addWidget(self.voice_combo)
            voice_layout.addStretch()
            layout.addLayout(voice_layout)
        
        # Speed selection
        if self.config.has_section('VoiceSpeed') and self.config.has_option('VoiceSpeed', 'SpeedChoices'):
            speed_layout = QHBoxLayout()
            speed_label = QLabel("Speed:")
            speed_label.setFixedWidth(60)
            self.speed_combo = QComboBox()
            
            speed_choices = self.config.get('VoiceSpeed', 'SpeedChoices', fallback='').split(',')
            speed_choices = [choice.strip() for choice in speed_choices if choice.strip()]
            self.speed_combo.addItems(speed_choices)
            
            # Set current selection if available
            if self.current_speed and self.current_speed in speed_choices:
                self.speed_combo.setCurrentText(self.current_speed)
                self.pending_speed = self.current_speed
            
            self.speed_combo.currentTextChanged.connect(self.on_speed_dropdown_changed)
            
            speed_layout.addWidget(speed_label)
            speed_layout.addWidget(self.speed_combo)
            speed_layout.addStretch()
            layout.addLayout(speed_layout)
        
        # Button layout - clean and simple
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(1)  # Same spacing as top buttons
        
        # Calculate button width: 2x the toolbar button size
        toolbar_button_size = int(self.config.get('Appearance', 'button_size', fallback='40'))
        control_button_width = toolbar_button_size * 2
        
        # Create the three buttons
        ok_button = QPushButton("OK")
        ok_button.setFixedSize(QSize(control_button_width, toolbar_button_size))
        ok_button.setFlat(False)  # Ensure it's a normal button
        ok_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #666;
                border-radius: 4px;
                background-color: #333;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                text-align: center;
                padding: 0px;
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
        ok_button.clicked.connect(self.collapse_options)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedSize(QSize(control_button_width, toolbar_button_size))
        cancel_button.setFlat(False)
        cancel_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #666;
                border-radius: 4px;
                background-color: #333;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                text-align: center;
                padding: 0px;
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
        cancel_button.clicked.connect(self.cancel_changes)
        
        quit_button = QPushButton("Quit")
        quit_button.setFixedSize(QSize(control_button_width, toolbar_button_size))
        quit_button.setFlat(False)
        quit_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #666;
                border-radius: 4px;
                background-color: #333;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                text-align: center;
                padding: 0px;
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
        quit_button.clicked.connect(self.confirm_quit)
        
        # Add buttons to layout
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button) 
        button_layout.addWidget(quit_button)
        layout.addLayout(button_layout)
        
        expanded_widget.setLayout(layout)
        return expanded_widget
    
    def on_voice_dropdown_changed(self, choice):
        """Handle voice dropdown change (not applied yet)"""
        self.pending_voice = choice
        
        # Check if this voice has a speed default
        if choice and self.config.has_section('SpeedDefaults'):
            default_speed = self.config.get('SpeedDefaults', choice, fallback=None)
            if default_speed and hasattr(self, 'speed_combo'):
                # Find the speed in the dropdown and select it
                speed_index = self.speed_combo.findText(default_speed)
                if speed_index >= 0:
                    self.speed_combo.setCurrentIndex(speed_index)
                    self.pending_speed = default_speed
        
    def on_speed_dropdown_changed(self, choice):
        """Handle speed dropdown change (not applied yet)"""
        self.pending_speed = choice
        
    def apply_pending_changes(self):
        """Apply any pending voice/speed changes"""
        from PyQt6.QtCore import QTimer
        
        commands_to_execute = []
        
        # Check if voice changed
        if self.pending_voice and self.pending_voice != self.current_voice:
            if self.config.has_option('VoiceSpeed', 'VoiceChange'):
                command = self.config.get('VoiceSpeed', 'VoiceChange')
                command = command.replace('{choice}', self.pending_voice)
                commands_to_execute.append(('voice', command))
                self.current_voice = self.pending_voice
        
        # Check if speed changed  
        if self.pending_speed and self.pending_speed != self.current_speed:
            if self.config.has_option('VoiceSpeed', 'SpeedChange'):
                command = self.config.get('VoiceSpeed', 'SpeedChange')
                command = command.replace('{choice}', self.pending_speed)
                commands_to_execute.append(('speed', command))
                self.current_speed = self.pending_speed
        
        # Execute commands with delay
        if commands_to_execute:
            self.execute_commands_with_delay(commands_to_execute)
            
        # Save settings
        if self.current_voice or self.current_speed:
            self.save_current_settings()
    
    def execute_commands_with_delay(self, commands):
        """Execute a list of commands with delays between them"""
        from PyQt6.QtCore import QTimer
        
        if not commands:
            return
            
        def execute_next_command(index=0):
            if index < len(commands):
                cmd_type, command = commands[index]
                try:
                    subprocess.Popen(command, shell=True)
                    print(f"Executed {cmd_type} command: {command}")
                except Exception as e:
                    print(f"Error executing {cmd_type} command: {e}")
                
                # Schedule next command if there are more
                if index + 1 < len(commands):
                    delay = int(self.config.get('Behavior', 'InitializationDelay', fallback='2000'))
                    QTimer.singleShot(delay, lambda: execute_next_command(index + 1))
        
        execute_next_command()
    
    def initialize_settings(self):
        """Initialize voice and speed settings on startup"""
        from PyQt6.QtCore import QTimer
        
        remember_settings = self.config.getboolean('Behavior', 'Remember_Voice_and_Speed', fallback=True)
        if not remember_settings:
            return
            
        commands_to_execute = []
        
        # Check if we have settings to initialize
        if self.current_voice and self.config.has_option('VoiceSpeed', 'VoiceChange'):
            command = self.config.get('VoiceSpeed', 'VoiceChange')
            command = command.replace('{choice}', self.current_voice)
            commands_to_execute.append(('voice', command))
            
        if self.current_speed and self.config.has_option('VoiceSpeed', 'SpeedChange'):
            command = self.config.get('VoiceSpeed', 'SpeedChange')
            command = command.replace('{choice}', self.current_speed)
            commands_to_execute.append(('speed', command))
        
        if commands_to_execute:
            self.initializing = True
            self.init_label.show()
            self.adjustSize()
            self.setFixedSize(self.size())
            
            def finish_initialization():
                self.initializing = False
                self.init_label.hide()
                self.adjustSize()
                self.setFixedSize(self.size())
            
            # Calculate total time needed
            delay = int(self.config.get('Behavior', 'InitializationDelay', fallback='2000'))
            total_time = len(commands_to_execute) * delay
            
            # Execute commands
            self.execute_commands_with_delay(commands_to_execute)
            
            # Hide initialization message after all commands complete
            QTimer.singleShot(total_time, finish_initialization)
        
    def save_current_settings(self):
        """Save current voice and speed selections to INI file"""
        if not self.config.has_section('CurrentSettings'):
            self.config.add_section('CurrentSettings')
        
        self.config.set('CurrentSettings', 'current_voice', self.current_voice or '')
        self.config.set('CurrentSettings', 'current_speed', self.current_speed or '')
        
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
        except Exception as e:
            print(f"Error saving current settings: {e}")
        
    def expand_options(self):
        """Expand the options panel"""
        if self.expanded:
            return
            
        self.expanded = True
        self.expanded_widget = self.create_expanded_widget()
        
        # Set pending values to current values when opening
        self.pending_voice = self.current_voice
        self.pending_speed = self.current_speed
        
        self.main_layout.addWidget(self.expanded_widget)
        
        # Check if animation is enabled
        animate = self.config.getboolean('Appearance', 'animation', fallback=True)
        
        if animate:
            # Set up animation
            self.expanded_widget.setMaximumHeight(0)
            self.animation = QPropertyAnimation(self.expanded_widget, b"maximumHeight")
            self.animation.setDuration(200)
            self.animation.setStartValue(0)
            self.animation.setEndValue(120)  # Adjust based on content
            self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.animation.start()
        else:
            self.expanded_widget.setMaximumHeight(120)
            
        # Adjust window size
        self.adjustSize()
        self.setFixedSize(self.size())
        
    def collapse_options(self):
        """Collapse the options panel and apply changes (OK button / right-click)"""
        if not self.expanded or not self.expanded_widget:
            return
        
        # Apply any pending changes before collapsing
        self.apply_pending_changes()
            
        animate = self.config.getboolean('Appearance', 'animation', fallback=True)
        
        if animate:
            self.animation = QPropertyAnimation(self.expanded_widget, b"maximumHeight")
            self.animation.setDuration(200)
            self.animation.setStartValue(self.expanded_widget.height())
            self.animation.setEndValue(0)
            self.animation.setEasingCurve(QEasingCurve.Type.InCubic)
            self.animation.finished.connect(self.remove_expanded_widget)
            self.animation.start()
        else:
            self.remove_expanded_widget()
            
    def cancel_changes(self):
        """Cancel changes and collapse without applying (Cancel button)"""
        if not self.expanded or not self.expanded_widget:
            return
            
        # Reset pending values to current values (discard changes)
        self.pending_voice = self.current_voice
        self.pending_speed = self.current_speed
        
        # Update dropdowns to show current values (revert any changes)
        if hasattr(self, 'voice_combo') and self.current_voice:
            self.voice_combo.setCurrentText(self.current_voice)
        if hasattr(self, 'speed_combo') and self.current_speed:
            self.speed_combo.setCurrentText(self.current_speed)
        
        # Collapse without applying changes
        animate = self.config.getboolean('Appearance', 'animation', fallback=True)
        
        if animate:
            self.animation = QPropertyAnimation(self.expanded_widget, b"maximumHeight")
            self.animation.setDuration(200)
            self.animation.setStartValue(self.expanded_widget.height())
            self.animation.setEndValue(0)
            self.animation.setEasingCurve(QEasingCurve.Type.InCubic)
            self.animation.finished.connect(self.remove_expanded_widget)
            self.animation.start()
        else:
            self.remove_expanded_widget()
            
    def cancel_changes(self):
        """Cancel changes and collapse without applying"""
        # Reset pending values to current values
        self.pending_voice = self.current_voice
        self.pending_speed = self.current_speed
        
        # Update dropdowns to show current values (not pending changes)
        if hasattr(self, 'voice_combo') and self.current_voice:
            self.voice_combo.setCurrentText(self.current_voice)
        if hasattr(self, 'speed_combo') and self.current_speed:
            self.speed_combo.setCurrentText(self.current_speed)
        
        # Collapse without applying changes
        self.collapse_options_without_applying()
        
    def collapse_options_without_applying(self):
        """Collapse the options panel without applying changes"""
        if not self.expanded or not self.expanded_widget:
            return
            
        animate = self.config.getboolean('Appearance', 'animation', fallback=True)
        
        if animate:
            self.animation = QPropertyAnimation(self.expanded_widget, b"maximumHeight")
            self.animation.setDuration(200)
            self.animation.setStartValue(self.expanded_widget.height())
            self.animation.setEndValue(0)
            self.animation.setEasingCurve(QEasingCurve.Type.InCubic)
            self.animation.finished.connect(self.remove_expanded_widget)
            self.animation.start()
        else:
            self.remove_expanded_widget()
            
    def remove_expanded_widget(self):
        """Remove the expanded widget after animation"""
        if self.expanded_widget:
            self.main_layout.removeWidget(self.expanded_widget)
            self.expanded_widget.deleteLater()
            self.expanded_widget = None
            
        self.expanded = False
        self.adjustSize()
        self.setFixedSize(self.size())
        
    def confirm_quit(self):
        """Show quit confirmation dialog or quit directly"""
        confirm_quit = self.config.getboolean('Behavior', 'ConfirmQuit', fallback=True)
        
        if confirm_quit:
            reply = QMessageBox.question(self, 'Quit Toolbar', 
                                       'Quit the toolbar?',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.quit_application()
        else:
            self.quit_application()
    
    def quit_application(self):
        """Handle the actual quit process"""
        # Check if we should clear settings on quit
        remember_settings = self.config.getboolean('Behavior', 'Remember_Voice_and_Speed', fallback=True)
        if not remember_settings:
            self.clear_current_settings()
        QApplication.quit()
    
    def clear_current_settings(self):
        """Clear current voice and speed settings from INI file"""
        if self.config.has_section('CurrentSettings'):
            self.config.remove_section('CurrentSettings')
            try:
                with open(self.config_file, 'w') as f:
                    self.config.write(f)
            except Exception as e:
                print(f"Error clearing current settings: {e}")
        
    def execute_command(self, command_key):
        """Execute the command associated with the button"""
        try:
            # Handle play/pause state logic
            if command_key == 'play':
                if self.play_state == "paused":
                    # If paused, resume instead of play
                    command = self.config.get('Commands', 'resume', fallback='')
                    if command:
                        subprocess.Popen(command, shell=True)
                        self.play_state = "playing"
                        print(f"Resumed playback, state: {self.play_state}")
                else:
                    # Not playing or unknown - start/restart playback
                    command = self.config.get('Commands', 'play', fallback='')
                    if command:
                        subprocess.Popen(command, shell=True)
                        self.play_state = "playing"
                        print(f"Started/restarted playback, state: {self.play_state}")
                return
                    
            elif command_key == 'pause':
                if self.play_state == "playing":
                    # Playing, so pause
                    command = self.config.get('Commands', 'pause', fallback='')
                    if command:
                        subprocess.Popen(command, shell=True)
                        self.play_state = "paused"
                        print(f"Paused playback, state: {self.play_state}")
                elif self.play_state == "paused":
                    # Already paused, resume
                    command = self.config.get('Commands', 'resume', fallback='')
                    if command:
                        subprocess.Popen(command, shell=True)
                        self.play_state = "playing"
                        print(f"Resumed from pause button, state: {self.play_state}")
                else:
                    # Not playing/paused - treat as pause command anyway
                    command = self.config.get('Commands', 'pause', fallback='')
                    if command:
                        subprocess.Popen(command, shell=True)
                        print(f"Executed pause command, keeping state: {self.play_state}")
                return
                    
            elif command_key == 'stop':
                # Stop playback and reset state
                command = self.config.get('Commands', 'stop', fallback='')
                if command:
                    subprocess.Popen(command, shell=True)
                    self.play_state = ""
                    print(f"Stopped playback, state: {self.play_state}")
                return
                
            elif command_key in ['rewind', 'fast_forward']:
                # Seeking - execute command and set state to playing
                command = self.config.get('Commands', command_key, fallback='')
                if command:
                    subprocess.Popen(command, shell=True)
                    self.play_state = "playing"
                    print(f"Seeking ({command_key}), state: {self.play_state}")
                return
                
            else:
                # Other commands (like record) don't affect play state
                command = self.config.get('Commands', command_key, fallback='')
                if command:
                    subprocess.Popen(command, shell=True)
                    print(f"Executed {command_key} command")
                else:
                    print(f"No command configured for {command_key}")
                    
        except Exception as e:
            print(f"Error executing command for {command_key}: {e}")
            
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
            
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.draggable = True
            self.drag_started = False
            self.offset = event.position().toPoint()
            self.press_pos = event.globalPosition().toPoint()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.draggable and self.offset is not None:
            current_pos = event.globalPosition().toPoint()
            if not self.drag_started:
                distance = (current_pos - self.press_pos).manhattanLength()
                if distance > 5:
                    self.drag_started = True
            
            if self.drag_started:
                self.move(current_pos - self.offset)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.draggable = False
            self.drag_started = False
            self.offset = None
            
    def contextMenuEvent(self, event):
        """Handle right-click to show expanded options"""
        if self.expanded:
            self.collapse_options()
        else:
            self.expand_options()

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
