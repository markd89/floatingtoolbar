# floatingtoolbar
Python GUI (Qt6) toolbar front-end to control the kokorodoki daemon

Kokorodoki provides a nice implementation of Kokoro TTS
https://github.com/eel-brah/kokorodoki 

When run in daemon mode, it waits for the client to pass it an action such as speak the text in the clipboard, stop playback, etc. The author suggests associating keyboard hotkeys for each action.

This python toolbar provides a UI alternative to using hotkeys.

<img width="165" height="36" alt="image" src="https://github.com/user-attachments/assets/9364ea53-3a23-4ad2-a27e-64aeffaaf15e" />

The included toolbar_config.ini allows you to configure what happens for each button.

New in version 1.1 is the ability to set voice and speed from within the application. Right click to display these options:

<img width="156" height="157" alt="image" src="https://github.com/user-attachments/assets/646d281a-351f-4590-84e0-b04cf3a2de41" />

then Right-click again to apply the changes to Voice and/or Speed.

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

# Options you may want to be aware of in the INI

[Behavior]

remember_voice_and_speed = 0/1

This causes voice and speed to be remembered between sessions. If you are controlling kokorodoki's speed/voice outside of the toolbar, you'll want to set this to 0.

Another option added in the ini allows you to set speed defaults for specific Voices. For example, I find the following useful:

[SpeedDefaults]

af_heart = 1.1

af_nicole = 1.4

[Appearance]

Set the default x, y location of the toolbar position on launch.
Adjust the button size.

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
