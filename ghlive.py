import usb.core
import usb.util
import time
import threading
import sys
from evdev import UInput, AbsInfo, ecodes as e

VENDOR_ID = 0x1430 # Mad Catz / RedOctane
PRODUCT_ID = 0x079b # GHLive Xbox One Dongle

# init packets
HORI_ACK_ID = bytearray([0x01, 0x20, 0x00, 0x09, 0x00, 0x04, 0x20, 0x3a, 0x00, 0x00, 0x00, 0x80, 0x00])
POWER_ON    = bytearray([0x05, 0x20, 0x00, 0x01, 0x00])
PDP_LED_ON  = bytearray([0x0a, 0x20, 0x00, 0x03, 0x00, 0x01, 0x14])
PDP_AUTH    = bytearray([0x06, 0x20, 0x00, 0x02, 0x01, 0x00])

# keep alive/magic poke
MAGIC_POKE = bytearray([0x22, 0x00, 0x00, 0x08, 0x02, 0x08, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00])

# dpad mapping
DPAD_MAP = {
    0: (0, -1),  1: (1, -1), 2: (1, 0),  3: (1, 1),
    4: (0, 1),   5: (-1, 1), 6: (-1, 0), 7: (-1, -1),
    8: (0, 0)
}

# config virtual controller
capabilities = {
    e.EV_KEY: [
        e.BTN_A, e.BTN_C, e.BTN_X, e.BTN_Y, e.BTN_Z, e.BTN_SELECT, 
        e.BTN_START, e.BTN_MODE, e.BTN_THUMBL, e.BTN_THUMBR
    ],
    e.EV_ABS: [
        (e.ABS_HAT0X, AbsInfo(0, -1, 1, 0, 0, 0)),
        (e.ABS_HAT0Y, AbsInfo(0, -1, 1, 0, 0, 0)),
        (e.ABS_Y,     AbsInfo(0, -32767, 32767, 16000, 512, 0)),
        (e.ABS_Z,     AbsInfo(0, -32767, 32767, 255, 512, 0)),
        (e.ABS_RZ,    AbsInfo(0, -32767, 32767, 255, 512, 0))
    ]
}

def keep_alive_thread(dev, endpoint_out):
    # send magic poke packet every 8 seconds to prevent disconnects
    while True:
        try:
            dev.write(endpoint_out.bEndpointAddress, MAGIC_POKE)
            time.sleep(8)
        except Exception as err:
            print(f"Keep-alive thread terminated: {err}")
            break

def main():
    print("Searching for GHLive Xbox One Dongle...")
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        print("Error: Dongle not found! Make sure it is plugged in.")
        sys.exit(1)

    if dev.is_kernel_driver_active(0):
        try:
            dev.detach_kernel_driver(0)
            print("Successfully detached from default kernel driver.")
        except usb.core.USBError:
            print("Error: Could not detach driver. Did you run with 'sudo'?")
            sys.exit(1)

    dev.set_configuration()
    cfg = dev.get_active_configuration()
    intf = cfg[(0,0)]

    ep_out = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
    ep_in = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)

    # increment the sequence number [2] for each consecutive packet
    try:
        HORI_ACK_ID[2] = 0
        dev.write(ep_out.bEndpointAddress, HORI_ACK_ID)
        time.sleep(0.05)

        POWER_ON[2] = 1
        dev.write(ep_out.bEndpointAddress, POWER_ON)
        time.sleep(0.05)

        PDP_LED_ON[2] = 2
        dev.write(ep_out.bEndpointAddress, PDP_LED_ON)
        time.sleep(0.05)

        PDP_AUTH[2] = 3
        dev.write(ep_out.bEndpointAddress, PDP_AUTH)
        print("Initialization packets sent\nDongle should be on")
    except Exception as err:
        print(f"Failed to initialize dongle: {err}")
        sys.exit(1)

    threading.Thread(target=keep_alive_thread, args=(dev, ep_out), daemon=True).start()

    print("Event loop running.\nGuitar is ready to shred!\n(Press Ctrl+C to exit)")

    with UInput(capabilities, name="GHLive Virtual Guitar", vendor=VENDOR_ID, product=PRODUCT_ID) as ui:
        while True:
            try:
                data = dev.read(ep_in.bEndpointAddress, 64, timeout=1000)

                if len(data) >= 11 and data[0] == 0x21:

                    # frets
                    ui.write(e.EV_KEY, e.BTN_A,      1 if (data[4] & 0x01) else 0)
                    ui.write(e.EV_KEY, e.BTN_C,      1 if (data[4] & 0x02) else 0)
                    ui.write(e.EV_KEY, e.BTN_X,      1 if (data[4] & 0x04) else 0)
                    ui.write(e.EV_KEY, e.BTN_Y,      1 if (data[4] & 0x08) else 0)
                    ui.write(e.EV_KEY, e.BTN_Z,      1 if (data[4] & 0x10) else 0)
                    ui.write(e.EV_KEY, e.BTN_SELECT, 1 if (data[4] & 0x20) else 0)

                    # dpad
                    dpad_val = data[6] & 0x0F
                    if dpad_val > 7:
                        dpad_val = 8
                    dpad_x, dpad_y = DPAD_MAP[dpad_val]
                    ui.write(e.EV_ABS, e.ABS_HAT0X, dpad_x)
                    ui.write(e.EV_ABS, e.ABS_HAT0Y, dpad_y)

                    # analog axes
                    strum_val = (data[8] - 128) * 512
                    tilt_val = (data[9] - 128) * 512
                    whammy_val = (data[10] - 128) * 512

                    ui.write(e.EV_ABS, e.ABS_Y, strum_val)
                    ui.write(e.EV_ABS, e.ABS_Z, tilt_val)
                    ui.write(e.EV_ABS, e.ABS_RZ, whammy_val)

                    # ui buttons
                    ui.write(e.EV_KEY, e.BTN_MODE,   1 if (data[5] & 0x01) else 0)
                    ui.write(e.EV_KEY, e.BTN_THUMBL, 1 if (data[5] & 0x02) else 0)
                    ui.write(e.EV_KEY, e.BTN_START,  1 if (data[5] & 0x04) else 0)
                    ui.write(e.EV_KEY, e.BTN_THUMBR, 1 if (data[5] & 0x10) else 0)

                    ui.syn()

            except usb.core.USBError as err:
                if err.errno == 110:
                    continue
                print(f"USB Error: {err}")
                break
            except KeyboardInterrupt:
                print("\nExiting...")
                break

if __name__ == '__main__':
    main()
