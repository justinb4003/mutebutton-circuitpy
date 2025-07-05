import time
import board
from digitalio import DigitalInOut, Direction, Pull
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
button = DigitalInOut(board.D7)
button.direction = Direction.INPUT
button.pull = Pull.UP  # Set the button to pull-up mode
keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)


off_value = button.value
on_value = not off_value
while True:
    led.value = button.value
    if on_value == button.value:
        print("Button pressed!\n")
        keyboard.press(Keycode.WINDOWS, Keycode.ALT, Keycode.K)
        keyboard.release_all()
        while button.value != off_value:
            time.sleep(0.1)
    time.sleep(0.1)