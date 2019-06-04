import time
from i2cdevice import Device, Register, BitField
from i2cdevice.adapter import Adapter, LookupAdapter, U16ByteSwapAdapter

__version__ = '0.0.1'


class SensorDataAdapter(Adapter):
    """Convert from 16-bit sensor data with crazy offset"""
    def __init__(self, bit_resolution=14):
        self.bit_resolution = bit_resolution

    def _encode(self, value):
        return value

    def _decode(self, value):
        LSB = (value & 0xFF00) >> 10
        MSB = (value & 0x00FF) << 6
        # print (bin(MSB),bin(LSB))
        return MSB + LSB


class BCDAdapter(Adapter):

    def _decode(self, value):
        upper = ((value & 0xF0) >> 4) * 10
        lower = (value & 0x0F)

        return upper + lower

    def _encode(self, value):
        upper = (int(value / 10)) << 4
        lower = value % 10

        return upper | lower


class InterruptLookupAdapter(Adapter):
    """Special version of the
    look up adapter that
    allows for multiple
    values to be set at once"""
    def __init__(self, lookup_table):
        self.lookup_table = lookup_table

    def _decode(self, value):
        return_list = []

        for bit_index in range(8):
            if (value & (1 << bit_index) != 0):
                index = list(self.lookup_table.values()).index(1 << bit_index)
                return_list.append(list(self.lookup_table.keys())[index])

        return return_list

    def _encode(self, value):
        return_value = 0x00

        try:
            for item in value:
                return_value = return_value | self.lookup_table[item]
        except TypeError:
            raise ValueError('Interrupt settings require a list')

        return return_value


class VEML6075:
    def __init__(self, i2c_addr=0x10, i2c_dev=None):
        self._i2c_addr = i2c_addr
        self._i2c_dev = i2c_dev
        self._is_setup = False
        # Device definition
        self._veml6075 = Device([0x10], i2c_dev=self._i2c_dev, bit_width=8, registers=(
            Register('UV_CONF', 0x00, fields=(
                BitField('value', 0xFFFF),
                BitField('uv_integration_time', 0b0111000000000000, adapter=LookupAdapter({
                    '50ms': 0b000,
                    '100ms': 0b001,
                    '200ms': 0b010,
                    '400ms': 0b011,
                    '800ms': 0b100
                })),
                BitField('high_dynamic_enable', 0b0000100000000000),
                BitField('trigger_measurement', 0b0000010000000000),
                BitField('enable_trigger_mode', 0b0000001000000000),
                BitField('shutdown', 0b0000000100000000)
            ), bit_width=16),
            Register('UVA_DATA', 0x07, fields=(
                BitField('data', 0xFFFF, adapter=U16ByteSwapAdapter()),
            ), bit_width=16),
            Register('UVB_DATA', 0x09, fields=(
                BitField('data', 0xFFFF, adapter=U16ByteSwapAdapter()),
            ), bit_width=16),
            Register('UVCOMP1_DATA', 0x0A, fields=(
                BitField('data', 0xFFFF, adapter=U16ByteSwapAdapter()),
            ), bit_width=16),
            Register('UVCOMP2_DATA', 0x0B, fields=(
                BitField('data', 0xFFFF, adapter=U16ByteSwapAdapter()),
            ), bit_width=16),
            Register('ID', 0x0C, fields=(
                BitField('device_id', 0xFFFF, adapter=U16ByteSwapAdapter()),
            ), bit_width=16),

        ))

    def get_integration_time(self):

        return self._veml6075.UV_CONF.get_uv_integration_time()

    def set_integration_time(self, value):
        try:
            self._veml6075.UV_CONF.set_uv_integration_time(value)
        except RuntimeError:
            raise RuntimeError('{0} is an invalid setting for UV integration time'.format(value))

    def get_id(self):

        return self._veml6075.ID.get_device_id()

    def get_shutdown(self):

        return self._veml6075.UV_CONF.get_shutdown()

    def set_shutdown(self, value):
        self._veml6075.UV_CONF.set_shutdown(value)

    def set_high_dynamic_range(self, value):
        self._veml6075.UV_CONF.set_high_dynamic_enable(value)

    def get_measurements(self):
        return self._veml6075.UVA_DATA.get_data(), self._veml6075.UVB_DATA.get_data()

    def get_comparitor_readings(self):

        return self._veml6075.UVCOMP1_DATA.get_data(), self._veml6075.UVCOMP2_DATA.get_data()

    def convert_to_index(self, uva, uvb, uv_comp1, uv_comp2):
        result = 0
        # These values can be adjusted for calibration
        uva_calib = 1
        uvb_calib = 1
        uv_comp1_calib = 1
        uv_comp2_calib = 1
        '''Coefficients for open air sensor and thin Teflon diffuser up to 0.25mm
        For diffuser thickness of 0.4 mm and 0.7 mm other / lower IR coefficients need to be used. These are: uva_b_coef = 1.17 and uvb_d_coef = 1.58.
        The visible cancellation coefficients stay the same.'''
        uva_a_coef = 2.22
        uva_b_coef = 1.33
        uvb_c_coef = 2.95
        uvb_d_coef = 1.74
        uva_response = 0.001461
        uvb_response = 0.002591
        uva_calc = uva - ((uva_a_coef * uva_calib * uv_comp1) / uv_comp1_calib) - ((uva_b_coef * uva_calib * uv_comp2) / uv_comp2_calib)
        uvb_calc = uvb - ((uvb_c_coef * uvb_calib * uv_comp1) / uv_comp1_calib) - ((uvb_d_coef * uvb_calib * uv_comp2) / uv_comp2_calib)
        uva_index = uva_calc * (1 / uva_calib) * uva_response
        uvb_index = uvb_calc * (1 / uvb_calib) * uvb_response
        result = (uva_index + uvb_index) / 2

        return uva_index, uvb_index, result


if __name__ == "__main__":
    import smbus

    bus = smbus.SMBus(1)

    uv_sensor = VEML6075(i2c_dev=bus)
    uv_sensor.set_shutdown(False)
    uv_sensor.set_high_dynamic_range(False)
    uv_sensor.set_integration_time('100ms')

    while 1:
        uva, uvb = uv_sensor.get_measurements()
        uv_comp1, uv_comp2 = uv_sensor.get_comparitor_readings()

        print('UVA : {0} UVB : {1} COMP 1 : {2} COMP 2 : {3}'.format(uva, uvb, uv_comp1, uv_comp2))
        print ('UVA INDEX: {0[0]} UVB INDEX : {0[1]} AVG UV INDEX : {0[2]}'.format(uv_sensor.convert_to_index(uva, uvb, uv_comp1, uv_comp2)))

        time.sleep(0.2)
