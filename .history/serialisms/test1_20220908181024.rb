fund = 2.5
range = 8
arr = []

def construct_fibonacci_matrix(fund, range, arr)
    sub_arr = []
    if fund == 0
        i = 1
        range.times do
            arr << fund
            i, fund = fund, i + fund
        end
    else
        i = fund
        range.times do
        arr << i
        i, fund = fund, i + fund
        end
    end
    arr.each do |y|
    x = []
    if y == 0
        i = 1
        arr.length.times do
            x << y 
            y, i = i, y + i
        end
    else
        i = 0
        arr.length.times do 
            x << y
            i, y = y, i + y
        end 
    end
        sub_arr << x
    end
    arr.replace(sub_arr)
end

construct_fibonacci_matrix(fund, range, arr)

p arr