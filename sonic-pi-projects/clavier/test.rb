arr = [60, 64, 67, 72, 76]

measures = []
# def test(arr)
#   # measures = []
#   measures.push(arr)
#   puts measures
# end
# end

# test(arr)

def inversion(r, m)
  i = 0
  m << r[i]
  while i < r.length
    y = 1
    while y < r.length
      if r[i] < r[y]
        x = r[y] - r[i]
        m << r[i] - x
      else
        return  
      end
      y += 1
    end
    i += 1
  end
end
# arr.each do |n| 
#   inversion(n)
# end
inversion(arr, measures)

p measures