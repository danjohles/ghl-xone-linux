# ghl-xone-linux
A Python-based Linux driver/wrapper for the Guitar Hero Live Xbox One USB dongle. Allows use of the 6-fret guitar in e.g. Clone Hero.
This script intercepts the raw USB packets from the GHL Xbox One dongle and translates them into standard Linux gamepad events (`uinput`). This allows the Linux operating system to recognize the 6-fret guitar, strum bar, and tilt sensors as a standard game controller.

## Requirements
* Python 3.x
* Linux Operating System (Native, SteamOS, or Bazzite)
* Required Python modules: `pyusb` and `evdev`

## Installation

1. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/danjohles/ghl-xone-linux
   cd ghl-xone-linux
2. Install the required Python dependencies
   ```bash
   pip install --user -r requirements.txt
## Usage & Testing
   
   Because this script directly interfaces with USB hardware and creates a virtual input device at the kernel level, it must be run with root privileges
   1. Insert your GHL Xbox One USB dongle into your PC - the dongle will be turned off
   2. Run the script from your terminal:
      ```bash
      sudo python3 ghlive.py
      ```
      *If you are on an immutable distro like Bazzite, run it like this instead:*
      ```bash
      sudo env PYTHONPATH=$(python3 -m site --user-site) python3 /path/to/script/ghlive.py
      ```
   3. The dongle will light up and is ready to sync the Guitar. Press the sync button on the dongle, then press the sync button on your Guitar to pair them if it is your first time connecting them.
   All subsequent times, it is enough to press the "home" button on the Guitar
   4. Play whatever you want to play with it. The guitar will now be recognized as a standard gamepad
   5. Unplug the dongle or press ctrl+c to stop the script when you're done
  
  ## Credits 
This project was heavily inspired by the original C implementation and reverse-engineering work done in the [paroj/xpad](https://github.com/paroj/xpad) Linux kernel module. Their foundational work in mapping the GHL dongle's USB packet structure made this Python port possible.
   
