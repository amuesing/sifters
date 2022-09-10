fund = 0
range = 8
arr = []

def construct_fibonacci_matrix(arr)

    x = []
    arr.each do |y|
        sub_arr = []
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
        x << sub_arr
    end
        arr.replace(x)
end

construct_fibonacci_matrix(arr)

p arr