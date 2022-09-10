
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