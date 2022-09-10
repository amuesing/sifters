#def generate_partials (fund, range) #spectrum_generator (fundamental, range of partials)

a = 440
r = 12
y = []
i = 1.0

r.times do
    i = 1
    x = a*i
    y << x
    i += 1
end

p y