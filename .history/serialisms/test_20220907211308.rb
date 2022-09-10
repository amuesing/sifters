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

# range = 10
# i = 0
# y = y

# range.times do 
#     p i
#     i, y = y, i + y
# end
end