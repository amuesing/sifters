#def generate_partials (fund, range) #spectrum_generator (fundamental, range of partials)

a = 440
r = 12
y = []
i = 1.0


r.times {|i|}
    i = 1
    x = a*i
    p x
    i += 1


puts r.length