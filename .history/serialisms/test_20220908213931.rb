row = [1,2,3,4,5]

def generate_serial_matrix(row)
    interval = []
    collumns = []
    z = []
    row.each do |tone|
        interval << (tone - row.first)
        collumns << Array.new(row.length) {row.first + (row.first - tone)}
    end
    collumns.each do |n| 
        z << collumns.zip(interval).map(&:sum)
    end
    row.replace(z)
end

generate_serial_matrix(row)

p row