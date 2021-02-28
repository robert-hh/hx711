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
                                   sideset_base=self.pSCK, in_base=self.pOUT)
        self.set_gain(gain);


    @rp2.asm_pio(
        sideset_init=rp2.PIO.OUT_LOW,
        in_shiftdir=rp2.PIO.SHIFT_LEFT,
        autopull=False,
        autopush=False,
    )
    def hx711_pio():
        wait(0, pin, 0)     .side (0)   # wait for the device being ready
        pull()              .side (0)   # get the number of clock cycles
        mov(x, osr)         .side (0)
        label("loop")
        nop()               .side (1)   # active edge
        in_(pins, 1)        .side (1)   # get the pin and shift it in
        jmp(x_dec, "loop")  .side (0)   # test for more bits
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

    def sm_expired(self, obj):
        self.sensor_fail = True        # set flas
        self.pOUT.init(Pin.OPEN_DRAIN) # reconfigure Pin
        self.pOUT.value(0)             # simulate ready signal

    def read(self):
        self.sensor_fail = False
        self.sm_timer.init(mode=Timer.ONE_SHOT, period=500, callback=self.sm_expired)
        # Feed the waiting state machine & get the data
        self.sm.active(1)  # start the state machine
        self.sm.put(self.GAIN + 24 - 1)     # set pulse count 25-27, start
        time.sleep_us(self.GAIN + 24)       # wait a while for the data
        result = self.sm.get() >> self.GAIN # get the result & discard GAIN bits
        self.sm.active(0)  # start the state machine
        self.sm_timer.deinit()
        if self.sensor_fail:
            self.pOUT.value(1)  # take back stress
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
