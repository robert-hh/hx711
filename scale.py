from machine import SPI, Pin
from hx711 import HX711

pin_OUT = Pin("P9", Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin("P10", Pin.OUT)

spi = SPI(0, mode=SPI.MASTER, baudrate=1000000, polarity=0,
             phase=0, pins=(None, pin_SCK, pin_OUT))

hx = HX711(pin_SCK, pin_OUT, spi)
hx.set_scale(48.36)
hx.tare()
val = hx.get_units(5)
print(val)
