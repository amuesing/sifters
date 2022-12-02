from music21 import *

p = sieve.Sieve('((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@3)|(8@4)|(8@1&5@2)|(8@6&5@1)')
psa = sieve.PitchSieve('((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@3)|(8@4)|(8@1&5@2)|(8@6&5@1)')
# print(psa.sieveObject.segment(z=(psa.sieveObject.period())))
# print(psa.sieveObject.period())
p.setZRange(0, 200)


seg = psa.sieveObject.segment()
psa.sieveObject.setZRange(0, 40-1)
# print(p.segment())
print(psa.sieveObject.segment())