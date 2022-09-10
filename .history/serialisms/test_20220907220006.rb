arr = [2, 2, 4, 6, 10, 16, 26, 42]

arr.each do |y|
sub_arr = []
    if y == 0
        i = 1
        arr.length.times do
            sub_arr << y 
            y, i = i, y + i
        end
    else
        i = y
        y = y
        arr.length.times do 
            sub_arr << i
            i, y = y, i + y
        end 
    end
p sub_arr
end