import time
from i2cdevice import Device, Register, BitField
from i2cdevice.adapter import Adapter, LookupAdapter, U16ByteSwapAdapter
import datetime

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
    allows for multipule
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
            raise ValueError('interrupt settings require a list')

        return return_value

class VEML6075:
    def __init__(self, i2c_addr=0x26, i2c_dev=None):
        self._i2c_addr = i2c_addr
        self._i2c_dev = i2c_dev
        self._is_setup = False
        # Device definition
        self._veml6075 = Device([0x52], i2c_dev=self._i2c_dev, bit_width=16, registers=(
            Register('UV_CONF', 0x00, fields=(
                BitField('uv_intergration_time', 0x011100000000000000, adapter=LookupAdapter({
                    '50ms': 0b000,
                    '100ms': 0b001,
                    '200ms': 0b010,
                    '400ms': 0b011,
                    '800ms': 0b100
                    })),
                BitField('high_dynamic_enable', 0x000010000000000000),
                BitField('trigger_measurement', 0x000001000000000000),
                BitField('enable_trigger_mode', 0x000000100000000000),
                BitField('shutdown', 0x000000010000000000)
            )),
            Register('UVA_DATA', 0x07, fields=(
                BitField('data', 0xFFF, adapter=U16ByteSwapAdapter())
            )),
            Register('UVB_DATA', 0x07, fields=(
                BitField('data', 0xFFF, adapter=U16ByteSwapAdapter())
            )),
            Register('UVCOMP1_DATA', 0x07, fields=(
                BitField('data', 0xFFF, adapter=U16ByteSwapAdapter())
            )),
            Register('UVCOMP2_DATA', 0x07, fields=(
                BitField('data', 0xFFF, adapter=U16ByteSwapAdapter())
            )),
            Register('ID', 0x07, fields=(
                BitField('device_id', 0xFF)
                
            )),


            
            ))

'''
a = uva_a_coef = 2.22, which is the default value for the UVA VIS coefficient
b = uva_b_coef = 1.33, which is the default value for the UVA IR coefficient
c = uvb_c_coef = 2.95, which is the default value for the UVB VIS coefficient
d = uvb_d_coef = 1.74, which is the default value for the UVB IR coefficient
'''


        