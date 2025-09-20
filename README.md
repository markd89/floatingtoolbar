# floatingtoolbar
Python GUI (Qt6) toolbar front-end to control kokorodoki daemon

Kokorodoki provides a nice implementation of Kokoro TTS
https://github.com/eel-brah/kokorodoki 

When run in daemon mode, it waits for the client to pass it an action such as speak the text in the clipboard, stop playback, etc. The author suggests associating keyboard hotkeys for each action.

This python toolbar provides an alternative to hotkeys with this UI.

<img width="165" height="36" alt="image" src="https://github.com/user-attachments/assets/9364ea53-3a23-4ad2-a27e-64aeffaaf15e" />

The included toolbar_config.ini allows you to configure what happens for each button.

Following are the actions we will automate (copied from the kokorodoki repository)

## Send from clipboard
~/.venvs/kdvenv/bin/python3.12 ~/.local/bin/kdoki/src/client.py

## Stop playback 
~/.venvs/kdvenv/bin/python3.12 ~/.local/bin/kdoki/src/client.py --stop

## Pause playback
~/.venvs/kdvenv/bin/python3.12 ~/.local/bin/kdoki/src/client.py --pause

## Resume playback
~/.venvs/kdvenv/bin/python3.12 ~/.local/bin/kdoki/src/client.py --resume

## Skip to next sentence
~/.venvs/kdvenv/bin/python3.12 ~/.local/bin/kdoki/src/client.py --next

## Go back a sentence
~/.venvs/kdvenv/bin/python3.12 ~/.local/bin/kdoki/src/client.py --back

# Features
- Frameless, always-on-top design
- Configurable commands via INI file
- Unicode media control icons
- Drag to reposition

# Requirements
- Python 3.12
- PyQt6

# Installation

pip install PyQt6

clone the repository (or download the files)

python3 floatingtoolbar.py
