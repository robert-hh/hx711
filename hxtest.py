from machine import SPI, Pin
# from hx711_spi import *
from hx711_pio import *
# from hx711 import *

pin_OUT = Pin(7, Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin(6, Pin.OUT)
# spi_SCK = Pin(14)

# spi = SPI(0, mode=SPI.MASTER, baudrate=1000000, polarity=0,
             # phase=0, pins=(None, pin_SCK, pin_OUT))
# spi = SPI(1, baudrate=1000000, polarity=0,
#           phase=0, sck=spi_SCK, mosi=pin_SCK, miso=pin_OUT)

# hx = HX711(pin_SCK, pin_OUT, spi)
hx = HX711(pin_SCK, pin_OUT)

from utime import ticks_ms, ticks_diff, sleep, sleep_ms
from machine import Pin

hx.OFFSET = 0 # -150000
hx.set_gain(128)
sleep_ms(50)

data = [0 for _ in range(100)]

def get_median(hx, num=100):
    for _ in range(num):
        data[_] = hx.read()
    data.sort()
    return data[num // 2]

def run(loops = 100):
    start = ticks_ms()
    hx.set_gain(128)
    sleep_ms(50)
    resulta = get_median(hx, loops)
    hx.set_gain(32)
    sleep_ms(50)
    resultb = get_median(hx, loops)
    print(resulta, resultb)

def run100(loops=100, delay = 1):
    for _ in range (loops):
        run(100)
        if delay:
            sleep(delay)

def minmax(loops=10000, raw=True):
    hx.set_gain(128)
    middle = hx.read_average(min(loops, 1000))
    hx.filtered = middle
    middle = abs(middle) - hx.OFFSET
    cnt00003 = 0
    cnt0001 = 0
    cnt0003 = 0
    cnt001 = 0
    cnt003 = 0
    cnt010 = 0
    cntx = 0
    print ("Average", middle)
    for _ in range(loops):
        if raw is True:
            val = abs(hx.read()) - hx.OFFSET
        else:
            val = abs(hx.read_lowpass()) - hx.OFFSET
        if middle * (1 - 0.000003) < val < middle * (1 + 0.000003):
            cnt00003 += 1
        elif middle * (1 - 0.00001) < val < middle * (1 + 0.00001):
            cnt0001 += 1
        elif middle * (1 - 0.00003) < val < middle * (1 + 0.00003):
            cnt0003 += 1
        elif middle * (1 - 0.0001) < val < middle * (1 + 0.0001):
            cnt001 += 1
        elif middle * (1 - 0.0003) < val < middle * (1 + 0.0003):
            cnt003 += 1
        elif middle * (1 - 0.001) < val < middle * (1 + 0.001):
            cnt010 += 1
        else:
            cntx += 1
            print("Really out of band at %d: %d %x"  % (_, int(val), int(val)))

    print("+/- 0.0003%% %f\n+/- 0.001%% %f\n+/- 0.003%% %f\n+/- 0.01%% %f\n+/- 0.03%% %f\n+/- .1%%   %f\nBeyond:  %f" %
          (cnt00003/loops, cnt0001/loops, cnt0003/loops, cnt001/loops, cnt003/loops, cnt010/loops, cntx/loops))


# run()
# minmax(10000)
