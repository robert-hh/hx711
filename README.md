# HX711: Python class for the HX711 load cell

This is a very short and simple class. This lib includes two variants of the
module. One is using direct GPIO pin handling, the other uses SPI. Besides
the class instantiation, both variants offer the same methods.

## Constructor

### hx711 = HX711(data_pin, clock_pin, gain=128)

This is the GPIO constructor. data_pin and clock_pin are the names of the GPIO
pins used for the communication. clock_pin must not be an input-only pin.
gain is the setting of gain and channel of the load cell amplifier.
The default value of 128 also selects channel A.

### hx711 = HX711(data_pin, clock_pin, spi_clk, gain=128)

This is the SPI constructor. data_pin is the SPI MISO, clock_pin the SPI MOSI.
spi_clk must be assigned but will not be be used. Input-only pins must not be used for
clock_pin and spi_clk. gain is the setting of gain and channel of the load cell amplifier.
The default value of 128 also selects channel A.

## Methods

### hx711.set_gain(gain)

Sets the gain and channel configuration which is used for the next call of hx711.read()

|Gain|Channel|
|:-:|:-:|
|128|A|
|64|A|
|32|B|

### result = hx711.read()

Returns the actual raw value of the load cell. Raw means: not scaled, no offset
compensation.

### result = hx711.read_average(times=3)

Returns the raw value of the load cell as the average of times readings of The
raw value.

### result = hx711.read_lowpass()

Returns the actual value of the load cell fed through an one stage IIR lowpass
filter. The properties of the filter can be set with set_time_constant().

### rh = hx711.set_time_constant(value=None)

Set the time constant used by hx711.read_lowpass(). The range is 0-1.0. Smaller
values means longer times to settle and better smoothing.
If value is None, the actual value of the time constant is returned.

### value = hx711.get_value()

Returns the difference of the filtered load cell value and the offset, as set by hx711.set_offset() or hx711.tare()

### units = hx711.get_units()

Returns the value delivered by hx711.get_value() divided by the scale set by
hx711.set_scale().

### hx711.tare(times=15)

Determine the tare value of the load cell by averaging times raw readings.

### hx711.power_down()

Set the load cell to sleep mode.

### hx711.power_up()

Switch the load cell on again.

## Example

```
# Example for Pycom device.
# Connections:
# xxPy | HX711
# -----|-----------
# P9   |  data_pin
# P10  |  clock_pin
#

from hx711 import HX711

hx711 = HX711('P9', 'P10')

hx711.tare()
value = hx711.read()
value = hx711.get_value()
```
