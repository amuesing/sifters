arr = [0, 1, 1, 2, 3, 5, 8, 13]
def generate_fibonacci_matrix (arr)
    sub_arr = []
    arr.each do |y|
        if y == 0
            i = 1
            arr.length.times do
                sub_arr << y 
                y, i = i, y + i
            end
        else
            i = 0
            arr.length.times do 
                sub_arr << y
                i, y = y, i + y
            end 
        end
        arr.replace(sub_arr)
    end
end