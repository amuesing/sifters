matrix = [[60, 64, 67, 72, 76],
          [60, 62, 69, 74, 77],
          [59, 62, 67, 74, 77],
          [60, 64, 67, 72, 76]]

seq = []
measures = []

def inversion(r, m)
  i = 0
  y = 1
  m << r[i]
  while y < r.length
    if r[i] > r[y]
    x = r[i] - r[y]
    m << r[i] + x
    else # if r[i] < r[y]
      x = r[y] - r[i]
      m << r[i] - x #what if r[i] === r[y] (repeated note)
    end
    y += 1
  end
end


matrix.each do |r|
r.each do |t|
  seq << t
end
end

inversion(seq, measures)

p measures.each_slice(5).to_a