# Teams Mute Button

This is, essentially, a microcontroller project that maps a button to keyboard
combinations. A single button does two things depending on how long you hold it:

* **Short click** sends Ctrl+Shift+K, which toggles "raise hand" in Microsoft Teams.
* **Hold for 0.4 seconds** sends Win+Alt+K, which toggles the microphone mute at the
  Windows level (so it works no matter which app has focus). The mute fires as soon
  as you cross the 0.4 second mark; releasing the button after that does nothing.

The hold threshold is the `LONG_PRESS_SECONDS` constant at the top of `main.py`.

# Hardware

This has been built and tested on two different RP2040 boards. The same
```main.py``` runs on either one -- it works out at startup which pins the board
actually has, so there's nothing to edit when you swap between them.

| Board | Button pin | Status light |
|---|---|---|
| [Seeeduino XIAO RP2040](https://www.seeedstudio.com/XIAO-RP2040-v1-0-p-5026.html) | ```D7``` | plain single-colour LED (```board.LED```) |
| [Waveshare RP2040-Zero](https://www.waveshare.com/wiki/RP2040-Zero) | ```GP7``` | RGB NeoPixel on GP16 (```board.NEOPIXEL```) |

The RP2040-Zero is sold under a pile of different brand names -- Dweii and
others -- usually listed as an "RP2040 Zero" or "Pico developer board" with 2MB
of flash. They're all the same Waveshare design and take the same firmware.

Note that these two boards use completely different pin naming. The XIAO uses
Adafruit-style names (```D7```), while the RP2040-Zero only exposes the chip's
native names (```GP7```) and has no ```board.D7``` at all. If you want the button
on some other pin, edit the ```BUTTON_PIN_NAMES``` list at the top of
```main.py``` and put your pin first.

## Wiring

You want some kind of momentary push button switch. Wire one leg of the button
to ground and the other to the button pin for your board (```D7``` on the XIAO,
```GP7``` on the RP2040-Zero). No pull-up resistor is needed -- the code turns on
the chip's internal one.

### Xiao Pins
![xiao-mute](https://github.com/user-attachments/assets/8e199eb9-941e-478a-920d-380dc3132668)

### Waveshare Pins
![waveshare-mute](https://github.com/user-attachments/assets/54cf614d-b60a-4a6b-bc7f-4d6464763d8a)

![image](https://github.com/user-attachments/assets/e08c1a99-7914-419f-ab83-d86ab7d4c8a5)

## Status light

The onboard light is only a debugging aid, but it's a handy one -- you can test
your wiring by touching the button pin to any GND pin and watching it change,
before you solder anything up.

| Colour | Meaning |
|---|---|
| off | button not pressed |
| green | button down, still a short click -- letting go sends Ctrl+Shift+K |
| red | held past the threshold, the mute toggle has already been sent |

On boards with only a plain single-colour LED there are no colours to be had, so
it simply lights up while the button is down.

At power-on the light flashes green then red, about half a second each. That's a
self test: if you ground the button pin and nothing happens, you at least know
the light itself is working and it's your contact that isn't.

# Software Installation

## 1. Flash CircuitPython

The board must be flashed with CircuitPython for this code to work. The firmware
version used to build this was **10.3.1**. Grab the ```uf2``` for *your* board --
they are not interchangeable, and flashing the wrong one gives you a board that
boots fine but has all the wrong pins:

* XIAO RP2040: https://circuitpython.org/board/seeeduino_xiao_rp2040/
* Waveshare RP2040-Zero: https://circuitpython.org/board/waveshare_rp2040_zero/

To get the board into its bootloader, hold down the ```boot``` button, then press
and release ```reset```, and only then let go of ```boot```. The board appears as
a mountable drive called ```RPI-RP2```. Copy the ```uf2``` file onto it. The board
reboots on its own and comes back as a ```CIRCUITPY``` disk.

Two things that save a lot of fiddling with those tiny buttons:

* A **brand new board** with nothing flashed on it already comes up in bootloader
  mode when you plug it in. No buttons needed.
* A board **already running CircuitPython** can be told to reboot into the
  bootloader from the serial REPL, which is far easier than the button dance:

```python
import microcontroller
microcontroller.on_next_reset(microcontroller.RunMode.BOOTLOADER)
microcontroller.reset()
```

Flashing does *not* wipe the ```CIRCUITPY``` filesystem, so upgrading the
firmware on a board that's already set up leaves ```main.py``` and ```lib``` alone.

A board being flashed for the first time is different: there's no filesystem yet,
so CircuitPython creates one and drops a stock "Hello World" ```code.py``` into
it. Delete that file. CircuitPython runs ```code.py``` in preference to
```main.py```, so if you leave it there it will quietly shadow ours and the button
will do nothing.

## 2. Copy the code

Copy ```main.py``` and the ```lib``` folder onto the ```CIRCUITPY``` drive. It
reboots and is ready to use.

The ```lib``` folder holds:

* ```adafruit_hid/``` -- required on every board, this is what pretends to be a keyboard.
* ```neopixel.mpy``` and ```adafruit_pixelbuf.mpy``` -- only needed on boards
  whose status light is a NeoPixel, such as the RP2040-Zero. They're harmless on
  the XIAO, which never loads them.

These are compiled ```.mpy``` files and are tied to the major CircuitPython
version. The ones here are built for CircuitPython 10.x; if you flash a 9.x
firmware instead they won't load. Matching builds come from the
[Adafruit CircuitPython Bundle](https://circuitpython.org/libraries).

# Hacking

It's a python script and your computer can mount the drive with the running code on it. Any text editor can be used to open up the ```main.py``` file and you can alter the keystroke(s) sent there.
