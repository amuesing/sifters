require "matrix"
require "~/dev/sonic-pi-projects/serialisms/modules.rb"
row = [1,2,3,4,5]

def generate_serial_matrix(row)
    interval = []
    collumns = []
    matrix = []
    row.each do |tone|
        interval << (tone - row.first)
        collumns << Array.new(row.length) {row.first + (row.first - tone)}
    end
    collumns.each do |transposition| 
        matrix << transposition.zip(interval).map(&:sum)
    end
    row.replace(matrix)
end

generate_serial_matrix(row)

p row