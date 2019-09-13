#!/usr/bin/env python

import time
import veml6075
import smbus

print("""uv_readings.py - Starts up sensor and displays fresh readings every second
    Press Ctrl+C to exit.""")
bus = smbus.SMBus(1)

# Create VEML6075 instance and set up
uv_sensor = veml6075.VEML6075(i2c_dev=bus)
uv_sensor.set_shutdown(False)
uv_sensor.set_high_dynamic_range(False)
uv_sensor.set_integration_time('100ms')

while 1:
    uva, uvb = uv_sensor.get_measurements()
    uv_comp1, uv_comp2 = uv_sensor.get_comparitor_readings()
    uv_indices = uv_sensor.convert_to_index(uva, uvb, uv_comp1, uv_comp2)

    print('UVA : {0} UVB : {1} COMP 1 : {2} COMP 2 : {3}'.format(uva, uvb, uv_comp1, uv_comp2))
    print('UVA INDEX: {0[0]} UVB INDEX : {0[1]} AVG UV INDEX : {0[2]}\n'.format(uv_indices))

    time.sleep(0.2)
