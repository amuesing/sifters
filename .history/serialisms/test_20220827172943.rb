# f = 440*(2**((79 - 69)/12))

# p 2**((78 - 69)/12)

# f = 440*(2**((100-69)/12.to_f))
# p f/100

# p ((100-69)/12)

def noteToFreq(note) 
    a = 440
    p (a / 32.to_f) * (2 ** ((note - 9) / 12.to_f))
end

# noteToFreq(72)

 p 440/32.to_f