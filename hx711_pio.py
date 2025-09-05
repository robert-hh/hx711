# MIT License

# Copyright (c) 2021 

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

from machine import Pin, Timer
import time
import rp2

class HX711:
    def __init__(self, clock, data, gain=128, state_machine=0):
        self.clock = clock
        self.data = data
        self.clock.value(False)

        self.GAIN = 0
        self.OFFSET = 0
        self.SCALE = 1

        self.time_constant = 0.25
        self.filtered = 0
        self.sm_timer = Timer()

        # create the state machine
        self.sm = rp2.StateMachine(state_machine, self.hx711_pio, freq=1_000_000,
                                   sideset_base=self.clock, in_base=self.data,
                                   set_base=self.data, jmp_pin=self.data)

        self.set_gain(gain);


    @rp2.asm_pio(
        sideset_init=rp2.PIO.OUT_LOW,
        in_shiftdir=rp2.PIO.SHIFT_LEFT,
        autopull=False,
        autopush=False,
    )
    def hx711_pio():
        pull()              .side (0)   # get the number of clock cycles
        mov(x, osr)         .side (0)
        set(pindirs, 0)     .side (0)    # Initial set pin direction.
# Wait for a high level = start of the DATA pulse
        wait(1, pin, 0)     .side (0)
# Wait for a low level = DATA signal
        wait(0, pin, 0)     .side (0)[7]
        nop()               .side (0)[7] # wait a while with the first clock
        label("bitloop")
        nop()               .side (1)   # active edge
        nop()               .side (1)
        in_(pins, 1)        .side (0)   # get the pin and shift it in
        jmp(x_dec, "bitloop").side (0)  # test for more bits
        
        label("finish")
        push(block)         .side (0)   # no, deliver data and start over

    def __call__(self):
        return self.read()

    def set_gain(self, gain):
        if gain is 128:
            self.GAIN = 1
        elif gain is 64:
            self.GAIN = 3
        elif gain is 32:
            self.GAIN = 2

        self.read()
        self.filtered = self.read()

    def read(self):
        # Feed the waiting state machine & get the data
        self.sm.active(1)  # start the state machine
        self.sm.put(self.GAIN + 24 - 1)     # set pulse count 25-27, start
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < 500:
            # Wait for the result
            if self.sm.rx_fifo() > 0:
                break
        else:
            self.sm.active(0)  # stop the state machine
            raise OSError("sensor timeout")

        result = self.sm.get(None, self.GAIN) # get the result & discard GAIN bits
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
        self.clock.value(False)
        self.clock.value(True)

    def power_up(self):
        self.clock.value(False)
