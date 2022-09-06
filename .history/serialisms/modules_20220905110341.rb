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

fund = 1
range = 8
row = []

def construct_fibonacci_matrix(fund, range, row)
    i = 0
    x = []
    y = []
    z = []
    range.times do
        row << i
        r = i + fund
        i = fund
        fund = r
        #same as
        #i, y = y, i + y
    end

    row.each do |n|
        # do same as above but with n and fund for each iteration
        # x << (n - row.first)
        # x << Array(n)
        x << Array.new(range) {n}
    end

    # x.each do |m|
    #     m.each do |n|
    #         p n
    #     end
    # end

    row.replace(x)

    p row

end

construct_fibonacci_matrix(fund, range, row)

# a = []

# row.each do |i|
#     c = 0
#     range.times do 
#         a << c
#         r = c + i[0]
#         c = i[0]
#         i[0] = r
#     end
# end

# p a.each_slice(range).to_a
