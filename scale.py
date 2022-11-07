from machine import SPI, Pin
from hx711 import HX711

pin_OUT = Pin("P9", Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin("P10", Pin.OUT)

# Default assignment: sck=Pin(10), mosi=Pin(11), miso=Pin(8)
spi = SPI(0, baudrate=1000000)

hx = HX711(pin_SCK, pin_OUT, spi)
hx.set_scale(48.36)
hx.tare()
val = hx.get_units(5)
print(val)
