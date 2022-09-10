arr = [0, 1, 1, 2, 3, 5, 8, 13]

arr.each do |y|
    i = 1
    if y == 0
        p y 
        i, y = y, i + y
    end

range = 10
i = 0
y = y

range.times do 
    p i
    i, y = y, i + y
end
end