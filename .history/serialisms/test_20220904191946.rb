range = 10
i = 0
y = 1



range.times do |i|
    i, y = y, i + y
end