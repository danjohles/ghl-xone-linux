# Optional: Plug-and-Play with systemd

If you don't want to keep opening the terminal and run `sudo python3 ghlive.py` every time you want to play -

you can configure `udev` to detect when you plug the Guitar Hero Live dongle in and automatically launch the script in the background using `systemd` (apologies to the systemd haters). Unplug the dongle, and the script safely shuts itself down.

### Step 1: Find your Python Path
Because root background services don't know where your user installed the `evdev` and `pyusb` libraries, you need to find your exact Python site-packages path. 

Run this in your terminal:
```bash
python3 -m site --user-site
```
*Copy the output path (e.g., `/home/username/.local/lib/python3.11/site-packages`). You will need it for Step 2.*

---

### Step 2: Create the Background Service
Create the service file that tells Linux how to run the script:
```bash
sudo nano /etc/systemd/system/ghlive.service
```

Paste the following configuration. **Make sure to change `username` to your actual Linux username, and paste your Python path from Step 1**

```ini
[Unit]
Description=GHLive Xbox One Dongle Driver
After=network.target

[Service]
Type=simple
# Inject your user's python packages so the root process can read them
Environment="PYTHONPATH=/home/username/.local/lib/python3.11/site-packages"

# Path to the script
ExecStart=/usr/bin/python3 /home/username/path/to/ghlive.py

Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```
> **Note for Bazzite / Silverblue Users:** If you are using an immutable/atomic distro, you shouldn't use the `/home/` shortcut. You **have** to change both paths above to use the absolute `/var/home/username/...` structure, or systemd will block it.

---

### Step 3: Create the Hardware Trigger
Now we tell the kernel to fire that service the second the dongle is connected.
```bash
sudo nano /etc/udev/rules.d/99-ghlive.rules
```

Paste this exact line:
```text
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="1430", ATTR{idProduct}=="079b", TAG+="systemd", ENV{SYSTEMD_WANTS}="ghlive.service"
```
Save and exit.

---

### Step 4: Reload and Use
Tell Linux to refresh its hardware rules and services to see your new files:
```bash
sudo systemctl daemon-reload
sudo udevadm control --reload-rules
```

**Done.** Unplug the dongle and plug it back in. It should instantly light up, and be ready for use.
