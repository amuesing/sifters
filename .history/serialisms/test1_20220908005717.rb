fund = 0
range = 8
arr = []

def construct_fibonacci_matrix(fund, range, arr)
    i = 0
    y = fund
    if fund == 0
        i = 1
        range.times do
            arr << y
            i, y = y, i + y
        end
    else
        i = 0

    range.times do
        arr << i
        i, y = y, i + y
    end
end
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

construct_fibonacci_matrix(fund, range, arr)

p arr