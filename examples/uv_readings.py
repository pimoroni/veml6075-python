import time
import veml6075
import smbus

bus = smbus.SMBus(1)

uv_sensor = veml6075.VEML6075(i2c_dev=bus)
uv_sensor.set_shutdown(False)
uv_sensor.disable_high_dynamic_range()
uv_sensor.set_intergration_time('800ms')

while 1:
    uva, uvb = uv_sensor.get_measurements()
    uv_comp1, uv_comp2 = uv_sensor.get_commparitor_readings()

    print('UVA : {0} UVB : {1} COMP 1 : {2} COMP 2 : {3}'.format(uva, uvb, uv_comp1, uv_comp2))
    print ('UVA INDEX: {0[0]} UVB INDEX : {0[1]} AVG UV INDEX : {0[2]}'.format(uv_sensor.convert_to_index(uva, uvb, uv_comp1, uv_comp2)))

    time.sleep(0.2)
