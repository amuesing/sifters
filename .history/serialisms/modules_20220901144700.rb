require 'matrix'

def generate_matrix(row)
    x = []
    y = []
    z = []
    row.each do |n|
        x << (n - row.first)
        y << Array.new(row.length) {row.first + (row.first - n)}
    end
    y.each do |n| 
        z << n.zip(x).map(&:sum)
    end
    row.replace(z)
end

def midi_to_freq(row)
    f = []
    row.each do |n|
        n.each do |o|
    a = 440
    f << (a / 32.to_f) * (2 ** ((o - 9) / 12.to_f))
        end
    end
    row.replace(f.each_slice(row.length).to_a) 
end

x = [3, 4, 5]

row = Vector

# def generate_overtones (freq, range, row)
#     partial = 1
#     spectrum = []
#     range.times.each do |i|
#         spectrum << freq * partial.to_f
#         partial += 1
#     end
#     row.replace(spectrum)
    
# end


p row
# generate_overtones(440, 12)