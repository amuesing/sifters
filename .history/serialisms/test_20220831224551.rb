#def generate_partials (fund, range) #spectrum_generator (fundamental, range of partials)

a = 440
r = 12
y = []
x = 1


r.times.each do |i|
    puts a*x
    x += 1
end

{|i| puts a*x, x += 1}