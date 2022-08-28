# f = 440*(2**((79 - 69)/12))

# p 2**((78 - 69)/12)

# f = 440*(2**((100-69)/12.to_f))
# p f/100

# p ((100-69)/12)

def noteToFreq(note) 
    a = 440; //frequency of A (coomon value is 440Hz)
    rp (a / 32) * (2 ** ((note - 9) / 12));
end