# Teams Mute Button

This is, essentially, a microcontroller project that maps a button to a keyboard
combination. In the published form it hits a key combination (Win+Alt+K) that
toggles your mute status in Microsoft Teams.

# Hardware
This is built on a Seeeduino Xiao RP2040. https://www.seeedstudio.com/XIAO-RP2040-v1-0-p-5026.html

The board must be flashed with CircuitPython for this code to work. The firmware version used to build this was 9.2.3. You can download the firmware from here: https://circuitpython.org/board/seeeduino_xiao_rp2040/

You'll then want some kind of momentary push button switch. Wire one leg of the button to ground and the other to the D7 pin on the Xiao RP-2040.
![xiao-mute](https://github.com/user-attachments/assets/8e199eb9-941e-478a-920d-380dc3132668)

![image](https://github.com/user-attachments/assets/e08c1a99-7914-419f-ab83-d86ab7d4c8a5)

# Software Installation
Instructions on how to flash the firmware are above, but, essentially hook the board to your computer via USB, hold down the ```boot``` button then press the ```reset``` button. The board will then appear as a mountable drive. Mount the drive on your computer and copy the ```uf2``` firmware file to it. Once completed the board will reset and now appear as a ```CIRCUITPY``` disk that you can mount.

Once that's done copy the ```main.py``` and ```lib``` folder over. It will reboot and now be ready to use.

# Hacking

It's a python script and your computer can mount the drive with the running code on it. Any text editor can be used to open up the ```main.py``` file and you can alter the keystroke(s) sent there.
