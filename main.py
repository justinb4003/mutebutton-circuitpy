import time
import board
import usb_hid
from digitalio import DigitalInOut, Direction, Pull
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

# How long (in seconds) the button must be held down before we treat the press
# as a "long press" instead of a "short click". Tweak this to taste.
LONG_PRESS_SECONDS = 0.4

# Which pin the button is wired to. Boards disagree about pin naming, so we try
# a few spellings and use the first one that exists:
#   D7   - Seeeduino XIAO RP2040 (and most Adafruit-style boards)
#   GP7  - Waveshare RP2040-Zero and other "raw" RP2040 boards, which only
#          expose the chip's native GP0-GP29 names.
# If you wired the button somewhere else, just put that pin first in the list.
BUTTON_PIN_NAMES = ("D7", "GP7")

button_pin = None
for _name in BUTTON_PIN_NAMES:
    if hasattr(board, _name):
        button_pin = getattr(board, _name)
        print("Using button pin:", _name)
        break
if button_pin is None:
    raise RuntimeError("No usable button pin found; tried " + str(BUTTON_PIN_NAMES))

# ---------------------------------------------------------------------------
# Status indicator
#
# This is only ever a debugging aid, but it's a genuinely useful one: with this
# running you can test your wiring by touching the button pin to any GND pin
# and watching the light change, without soldering anything up first.
#
#   off    - button is not pressed
#   green  - button is down, but not yet long enough to count as a long press,
#            so letting go now sends the Teams raise-hand shortcut
#   red    - you've crossed LONG_PRESS_SECONDS and the mute toggle has been
#            sent; letting go now does nothing
#
# Boards differ in what they give us. The XIAO RP2040 has a plain single-colour
# LED, so it can only manage "lit" and "not lit". The RP2040-Zero has no plain
# LED at all, only an addressable RGB NeoPixel, which is where the colours come
# in. We support whichever one the board actually has.
# ---------------------------------------------------------------------------
STATUS_OFF = (0, 0, 0)
STATUS_PRESSED = (0, 255, 0)
STATUS_MUTED = (255, 0, 0)

led = None
pixel = None

if hasattr(board, "LED"):
    led = DigitalInOut(board.LED)
    led.direction = Direction.OUTPUT
    print("Status indicator: plain LED on board.LED")
elif hasattr(board, "NEOPIXEL"):
    try:
        import neopixel

        # Keep the brightness low. These things are startlingly bright at 1.0,
        # and we only need to be able to see it, not read by it.
        pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1, auto_write=True)
        print("Status indicator: NeoPixel on board.NEOPIXEL")
    except ImportError:
        print("NeoPixel found but the 'neopixel' library is missing from lib/.")
else:
    print("No status indicator on this board; running without one.")


def set_status(colour):
    """Show one of the STATUS_* colours on whatever indicator we found."""
    if pixel is not None:
        pixel[0] = colour
    elif led is not None:
        # A plain LED can't do colour, so anything that isn't "off" lights it.
        led.value = colour != STATUS_OFF


# The button is pulled up internally, so we read it as a digital input.
# When the button is closed, it will read LOW (False).
# When the button is not closed, it will read HIGH (True).
# NOTE: Being pressed and being closed are not always the same thing!
button = DigitalInOut(button_pin)
button.direction = Direction.INPUT
button.pull = Pull.UP

keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)


# Whatever state the button is in when we start, we will use that as the
# "off" state. When the button is pressed, it will be in the "on" state.
# The button may be 'closed' when the button is not pressed, and complete
# the circuit, so we'll default the off state to what it is on startup.
off_value = button.value
on_value = not off_value


def send_teams_raise_hand():
    """Ctrl+Shift+K: toggles the 'raise hand' state in Microsoft Teams."""
    print("Short click: sending Ctrl+Shift+K (Teams raise hand)\n")
    keyboard.press(Keycode.CONTROL, Keycode.SHIFT, Keycode.K)
    keyboard.release_all()


def send_windows_mute():
    """Win+Alt+K: toggles the system-wide microphone mute in Windows."""
    print("Long press: sending Win+Alt+K (Windows mute toggle)\n")
    keyboard.press(Keycode.WINDOWS, Keycode.ALT, Keycode.K)
    keyboard.release_all()


# Quick power-on self test: flash the indicator through its two working
# colours so you can see at a glance that the light is alive and which way
# round the colours go. This also means that if you touch the button pin to
# ground and nothing happens, you know the light isn't the problem.
set_status(STATUS_PRESSED)
time.sleep(0.4)
set_status(STATUS_MUTED)
time.sleep(0.4)
set_status(STATUS_OFF)
print("Ready. Touch the button pin to GND: green = short click, red = mute.")

# This is a microcontroller so we're just going to put this in an infinite loop
# and let it run until the power is turned off or the board is reset.
while True:
    if button.value == on_value:
        # Light up the moment we see the pin go low. This happens before the
        # debounce check on purpose, so that poking the pin against ground
        # gives you instant feedback while you're testing the wiring.
        set_status(STATUS_PRESSED)

        # Cheap debounce: wait a moment and make sure the button is still down
        # before we believe it. A bouncing contact will settle well inside this.
        time.sleep(0.02)
        if button.value != on_value:
            set_status(STATUS_OFF)
            continue

        press_started = time.monotonic()

        # True once we've already fired the mute toggle for this press, so we
        # only send it once no matter how long the button stays down.
        mute_sent = False

        # Sit here for as long as the button is held down. We watch the clock
        # while we wait so we can fire the mute toggle the instant we cross the
        # long-press threshold -- that gives immediate feedback rather than
        # making you wait until you let go.
        while button.value == on_value:
            if not mute_sent and (time.monotonic() - press_started) >= LONG_PRESS_SECONDS:
                send_windows_mute()
                mute_sent = True
                set_status(STATUS_MUTED)
            time.sleep(0.01)

        # The button is back up. If we never crossed the threshold this was a
        # short click, so that's the Teams raise-hand shortcut. If we did send
        # the mute toggle, releasing the button deliberately does nothing.
        if not mute_sent:
            send_teams_raise_hand()

        set_status(STATUS_OFF)

        # Let the contact settle after release so one press can't register twice.
        time.sleep(0.02)

    time.sleep(0.01)
