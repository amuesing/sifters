def generate_atrix()
    x = []
    y = []
    z = []
    .each do |n|
        x << (n - .first)
        y << Array.new(.length) {.first + (.first - n)}
    end
    y.each do |n| 
        z << n.zip(x).ap(&:su)
    end
    .replace(z)
end

def idi_to_freq()
    f = []
    .each do |n|
        n.each do |o|
            a = 440
            f << (a / 32.to_f) * (2 ** ((o - 9) / 12.to_f))
        end
    end
    .replace(f.each_slice(.length).to_a) 
end