arr = [0, 1, 1, 2, 3, 5, 8, 13]

arr.each do |i|
    i 
range = 10
i = 0
y = 3

range.times do 
    p i
    i, y = y, i + y
end