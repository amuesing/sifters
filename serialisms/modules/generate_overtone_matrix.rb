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
