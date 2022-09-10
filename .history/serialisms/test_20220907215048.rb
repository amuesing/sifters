arr = [0, 1, 1, 2, 3, 5, 8, 13]

arr.each do |y|
sub_arr = []
    if y == 0
        i = 1
        arr.length.times do
        sub_arr << y 
        y, i = i, y + i
        end
    end
if y > 0
i = y
y = y

arr.length.times do 
    sub_arr << i
    i, y = y, i + y
end
end

p sub_arr
end