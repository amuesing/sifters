def generate_matrix(row)
    x = []
    y = []
    z = []
    m.each do |n|
        x << (n - m.first)
        y << Array.new(row.length) {m.first + (m.first - n)}
    end
    y.each do |n| 
        z << n.zip(x).map(&:sum)
    end
    m.replace(z)
end

def midi_to_freq(m)
    f = []
    m.each do |n|
        n.each do |o|
    a = 440
    f << (a / 32.to_f) * (2 ** ((o - 9) / 12.to_f))
        end
    end
    m.replace(f.each_slice(m.length).to_a) 
end