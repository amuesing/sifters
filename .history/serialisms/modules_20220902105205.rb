#Generate an array where each indice is a 
#sequentially ordered partial of the overtone 
#series based off of a fundamental frequency, 
#and a range of included partials to be included.

def generate_overtones (freq, range, row)
    partial = 1
    overtones = []
    range.times.each do |i|
        overtones << freq * partial.to_f
        partial += 1
    end
    row.replace(overtones)
end

def generate_undertones (freq, range, row)
    partial = 1
    overtones = []
    range.times.each do |i|
        overtones << freq / partial.to_f
        partial += 1
    end
    row.replace(overtones)
end

$partial = 1

#a method which is inverted along a undertone series
def generate_overtone_matrix (freq, range, row)
    overtones = []

    range.times.each do |i|
        overtones << freq * partial.to_f
        partial += 1
    end
    row.replace(overtones)
    p overtones
    row.each do |i|
        partial = 1
        x << Array.new(row.length) {freq / partial.to_f}
        partial += 1
    end
    # p x
end

freq = 440
row = []

generate_overtone_matrix(freq, 5, row)

# p row

def generate_serial_matrix(row)
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


