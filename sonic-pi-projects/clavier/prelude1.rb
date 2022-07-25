# use_bpm 60
# use_synth :piano

# sixteen = 0.25
# two16 = 0.5
# seven16 = 1.75
# eight16 = 2

matrix = [[60, 64, 67, 72, 76],
          [60, 62, 69, 74, 77],
          [59, 62, 67, 74, 77],
          [60, 64, 67, 72, 76],
          [60, 64, 69, 76, 81],
          [60, 62, 66, 69, 74],
          [59, 62, 67, 74, 79],
          [59, 60, 64, 67, 72],
          [57, 60, 64, 67, 72],
          [50, 57, 62, 66, 72],
          [55, 59, 62, 67, 71],
          [55, 58, 64, 67, 73],
          [53, 57, 62, 69, 74],
          [53, 56, 62, 65, 71],
          [52, 55, 60, 67, 72],
          [52, 53, 57, 60, 65],
          [50, 53, 57, 60, 65],
          [43, 50, 55, 59, 65],
          [48, 52, 55, 60, 64],
          [48, 55, 58, 60, 64],
          [41, 53, 57, 60, 64],
          [42, 48, 57, 60, 63],
          [44, 53, 59, 60, 62],
          [43, 53, 55, 59, 62],
          [43, 52, 55, 60, 64],
          [43, 50, 55, 60, 65],
          [43, 50, 55, 59, 65],
          [43, 51, 57, 60, 66],
          [43, 52, 55, 60, 67],
          [43, 50, 55, 60, 65],
          [43, 50, 55, 59, 65],
          [36, 48, 55, 58, 64]]


measures = []


def retrograde(row)
  row.reverse.each.map { |note| note }
end

##| def inversion(row)
##|   puts row
##|   i = 0
##|   while i < row.length
##|     y = y + 1
##|     while y < row.length
##|       puts row[i] + row[y]
##|     end
##|     y += 1
##|   end
##|   i += 1
##| end

def inversion(row)
  i = 0
  while row[i] > row.length
    y = 1
    while row[1] > row.length
      puts "hi"
    end
    ##| x[i] - x[0] = y
    ##| puts x[0]-y
    i += 1
  end
  
end

matrix.each do |row|
  inversion(row)
end

##| matrix.each do |row|
##|   measures << retrograde(row)
##| end

# measures.each do |chord|
#   2.times do
#     in_thread do
#       play chord.at(0), decay: 0.25
#     end
#     in_thread do
#       sleep sixteen
#       play chord.at(1), decay: 0.75
#       sleep seven16
#     end
#     sleep two16
#     2.times do
#       chord[2..4].each do |note|
#         play note, decay: 0.75
#         sleep sixteen
#       end
#     end
#   end
# end

##| ##| last three measures

##| in_thread do
##|   play 36
##|   sleep 4
##| end
##| in_thread do
##|   sleep 0.25
##|   play 48
##|   sleep 3.75
##| end
##| sleep two16
##| play_pattern_timed [53, 57, 60, 65, 60, 57, 60, 57, 53, 57, 53, 50, 53, 50], [0.25]

##| in_thread do
##|   play 36
##|   sleep 4
##| end
##| in_thread do
##|   sleep 0.25
##|   play 47
##|   sleep 3.75
##| end
##| sleep two16
##| play_pattern_timed [67, 71, 74, 77, 74, 71, 74, 71, 67, 71, 62, 65, 64, 62], [0.25]

##| play 36
##| play 48
##| play 52
##| play 55
##| play 60
##| sleep 4
