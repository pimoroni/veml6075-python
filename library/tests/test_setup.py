import sys
from i2cdevice import MockSMBus
import mock


def test_setup():
    sys.modules['smbus'] = mock.Mock()
    sys.modules['smbus'].SMBus = MockSMBus

    import veml6075

    uv_sensor = veml6075.VEML6075()
    uv_sensor.set_shutdown(False)
    uv_sensor.set_high_dynamic_range(False)
    uv_sensor.set_integration_time('800ms')
    uva, uvb = uv_sensor.get_measurements()
    uv_comp1, uv_comp2 = uv_sensor.get_comparitor_readings()
    del uv_sensor
