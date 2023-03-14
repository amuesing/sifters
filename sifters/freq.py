from decimal import Decimal

# Given a fundamental, find an octave above, then segment that octave by a given modulo.

# f = 110
# mod = 3
# seg = f % mod
# print(seg)

# You need to grab the specific range between the fundamental and the octave in order to maintain consistency.

# def create_subdivided_list(fundamental, divisor):
#     octave = fundamental * 2
#     rng = octave - fundamental
#     interval = rng / divisor
#     return [i*interval for i in range(divisor)]

# num = create_subdivided_list(220, 3)
# print([220 + n for n in num])
# print(num)

# fund = 220
# oct = fund * 2

# def segment_octave_by_freq(fundamental, modulo):
#     interval = fundamental / modulo
#     return [i * interval + fund for i in range(modulo)]

# list = segment_octave_by_freq(fund, 40)

# print(list)

def segment_octave_by_period(period):
    interval = Decimal('12') / Decimal(str(period))
    return [float(interval * Decimal(str(i))) for i in range(period)]

seg = segment_octave_by_period(40)

print(seg)