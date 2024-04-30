import music21

# siv = '''
#         (((8@0|8@1|8@7)&(5@1|5@3))|
#         ((8@0|8@1|8@2)&5@0)|
#         ((8@5|8@6)&(5@2|5@3|5@4))|
#         (8@6&5@1)|
#         (8@3)|
#         (8@4)|
#         (8@1&5@2))
#         '''

siv = '''
        (3@2|7@1)
        '''

s = music21.sieve.Sieve(siv)

# period = s.period()

# s.setZRange(0, period - 1)

binary = s.segment(segmentFormat='binary')
width = s.segment(segmentFormat='width')
unit = s.segment(segmentFormat='unit')

count = 0

for i in binary:
    if binary[i] == 1:
        count += 1


# print(len(binary))
print(count)
# print(width)
print(len(unit))