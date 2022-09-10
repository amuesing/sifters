range = 10
i = 0
y = 3



range.times do 
    p i
    # i, y = y, i + y
    z = i + y
    i = y
    y = z
end