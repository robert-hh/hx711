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

from machine import idle
import time


class HX711:
    def __init__(self, clock, data, spi, gain=128):
        self.clock = clock
        self.data = data
        self.spi = spi

        self.clock(0)

        self.clock_25 = b'\xaa\xaa\xaa\xaa\xaa\xaa\x80'
        self.clock_26 = b'\xaa\xaa\xaa\xaa\xaa\xaa\xa0'
        self.clock_27 = b'\xaa\xaa\xaa\xaa\xaa\xaa\xa8'
        self.clock = self.clock_25
        self.lookup = (b'\x00\x01\x00\x00\x02\x03\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x04\x05\x00\x00\x06\x07\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x08\x09\x00\x00\x0a\x0b\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x0d\x00\x00'
                       b'\x0e\x0f')
        self.in_data = bytearray(7)

        self.OFFSET = 0
        self.SCALE = 1

        self.time_constant = 0.1
        self.filtered = 0

        self.set_gain(gain)

    def set_gain(self, gain):
        if gain is 128:
            self.clock = self.clock_25
        elif gain is 64:
            self.clock = self.clock_27
        elif gain is 32:
            self.clock = self.clock_26

        self.read()
        self.filtered = self.read()
        # print('Gain & initial value set')

    def read(self):
        # wait for the device to get ready
        for _ in range(500):
            if self.data() == 0:
                break
            time.sleep_ms(1)
        else:
            raise OSError("Sensor does not respond")

        # get the data and set channel and gain
        self.spi.write_readinto(self.clock, self.in_data)

        # pack the data into a single value
        result = 0
        for _ in range(6):
            result = (result << 4) + self.lookup[self.in_data[_] & 0x55]

        # return sign corrected result
        return result - ((result & 0x800000) << 1)

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

    def set_time_constant(self, time_constant=None):
        if time_constant is None:
            return self.time_constant
        elif 0 < time_constant < 1.0:
            self.time_constant = time_constant

    def power_down(self):
        self.clock.value(False)
        self.clock.value(True)

    def power_up(self):
        self.clock.value(False)
