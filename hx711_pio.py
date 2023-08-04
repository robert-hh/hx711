# MIT License

# Copyright (c) 2019 

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from machine import Pin, idle, Timer
import time
import rp2

class HX711:
    def __init__(self, clk, data, gain=128):
        self.pSCK = clk
        self.pOUT = data
        self.pSCK.value(False)

        self.GAIN = 0
        self.OFFSET = 0
        self.SCALE = 1

        self.time_constant = 0.25
        self.filtered = 0
        self.sm_timer = Timer()

        # create the state machine
        self.sm = rp2.StateMachine(0, self.hx711_pio, freq=1_000_000,
                                   sideset_base=self.pSCK, in_base=self.pOUT,
                                   jmp_pin=self.pOUT)
        self.set_gain(gain);


    @rp2.asm_pio(
        sideset_init=rp2.PIO.OUT_LOW,
        in_shiftdir=rp2.PIO.SHIFT_LEFT,
        autopull=False,
        autopush=False,
    )
    def hx711_pio():
        # wait(0, pin, 0)     .side (0)   # wait for the device being ready
        pull()              .side (0)   # get the initial wait time
        mov(y, osr)         .side (0)
        pull()              .side (0)   # get the number of clock cycles
        mov(x, osr)         .side (0)

        label("start")
        jmp(pin, "nostart") .side (0)   # not ready yet
        jmp("bitloop")      .side (0)   # ready, get data

        label("nostart")
        jmp(y_dec, "start") .side (0)   # another attempt
        mov(isr, y)         .side (0)   # set 0xffffffff as error value
        jmp("finish")       .side (0)

        label("bitloop")
        nop()               .side (1)   # active edge
        in_(pins, 1)        .side (1)   # get the pin and shift it in
        jmp(x_dec, "bitloop")  .side (0)   # test for more bits
        
        label("finish")
        push(block)         .side (0)   # no, deliver data and start over


    def set_gain(self, gain):
        if gain is 128:
            self.GAIN = 1
        elif gain is 64:
            self.GAIN = 3
        elif gain is 32:
            self.GAIN = 2

        self.read()
        self.filtered = self.read()

    def is_ready(self):
        return self.pOUT() == 0

    def read(self):
        # Feed the waiting state machine & get the data
        self.sm.active(1)  # start the state machine
        self.sm.put(250_000)     # set wait time to 500ms
        self.sm.put(self.GAIN + 24 - 1)     # set pulse count 25-27, start
        result = self.sm.get() >> self.GAIN # get the result & discard GAIN bits
        self.sm.active(0)  # stop the state machine
        if result == 0x7fffffff:
            raise OSError("Sensor does not respond")

        # check sign
        if result > 0x7fffff:
            result -= 0x1000000

        return result

    def read_average(self, times=3):
        sum = 0
        for i in range(times):
            sum += self.read()
        return sum / times

    def read_lowpass(self):
        self.filtered += self.time_constant * (self.read() - self.filtered)
        return self.filtered

    def get_value(self):
        return self.read_lowpass() - self.OFFSET

    def get_units(self):
        return self.get_value() / self.SCALE

    def tare(self, times=15):
        self.set_offset(self.read_average(times))

    def set_scale(self, scale):
        self.SCALE = scale

    def set_offset(self, offset):
        self.OFFSET = offset

    def set_time_constant(self, time_constant = None):
        if time_constant is None:
            return self.time_constant
        elif 0 < time_constant < 1.0:
            self.time_constant = time_constant

    def power_down(self):
        self.pSCK.value(False)
        self.pSCK.value(True)

    def power_up(self):
        self.pSCK.value(False)
