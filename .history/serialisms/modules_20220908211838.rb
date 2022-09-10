require 'prime'

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

#####

#Generate an array where each indice is a 
#sequentially ordered partial of the overtone 
#series based off of a fundamental frequency, 
#and a range of included partials to be included.

def generate_overtone_matrix (freq, range, row)
    partial = 1
    overtones = []
    subtones = []
    matrix = []

    range.times.each do |i|
        overtones << freq * partial.to_f
        partial += 1
    end

    partial = 1

    overtones.each do |i|
        subtones << Array.new(overtones.length) {freq / partial.to_f}
        partial += 1
    end

    subtones.each do |i|
        partial = 1
        i.each do |fund|
            matrix << fund * partial
            partial += 1
        end
    end

    row.replace(matrix.each_slice(range).to_a)
end

# Generate Fibonacci Matrix

def construct_fibonacci_sequence(fund, range, arr)
    i = 0
    y = fund
    range.times do
        arr << i
        i, y = y, i + y
    end
end

def construct_fibonacci_matrix(fund, range, arr)
    matrix = []
    if fund == 0
        i = 1
        range.times do
            arr << fund
            i, fund = fund, i + fund
        end
    else
        i = fund
        range.times do
        arr << i
        i, fund = fund, i + fund
        end
    end
    arr.each do |y|
    x = []
    if y == 0
        i = 1
        arr.length.times do
            x << y 
            y, i = i, y + i
        end
    else
        i = 0
        arr.length.times do 
            x << y
            i, y = y, i + y
        end 
    end
        matrix << x
    end
    arr.replace(matrix)
end

def select_primes(arr)
    arr.replace(arr.select {|n| n.prime?})
end