import time
import board
import usb_hid
from digitalio import DigitalInOut, Direction, Pull
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

# The board has an LED on it and we'll use that a bit for debugging; not really
# necessary for the main functionality of this code.
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT

# The button is connected to D7 and is pulled up internally, so we read it as
# a digital input. When the button is closed, it will read LOW (False).
# When the button is not closed, it will read HIGH (True).
# NOTE: Being pressed and being closed are not always the same thing!
button = DigitalInOut(board.D7)
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

# This is a microcontroller so we're just going to put this in an infinite loop
# and let it run until the power is turned off or the board is reset.
while True:
    # The only thing we use the LED for: if the button is closed turn the LED on
    led.value = button.value
    if on_value == button.value:
        # You won't see this output unless you have a serial console
        # connected to the board.
        print("Button pressed!\n")

        # Now we send our desired key combination to the host computer.
        keyboard.press(Keycode.WINDOWS, Keycode.ALT, Keycode.K)
        keyboard.release_all()
        # If we wanted to send text it would look like this:
        # layout.write("Hello, world!")

        # Now we're going to loop until the button is released.
        while button.value != off_value:
            time.sleep(0.1)

    time.sleep(0.1)