def midi_to_freq(matrix)
    freq = []
    matrix.each do |row|
        row.each do |tone|
            a = 440
            freq << (a / 32.to_f) * (2 ** ((tone - 9) / 12.to_f))
        end
    end
    matrix.replace(freq.each_slice(matrix.length).to_a) 
end