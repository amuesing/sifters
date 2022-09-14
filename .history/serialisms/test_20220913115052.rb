# def combos(n,k,min = 1, cache = {})
#     if n < k || n < min
#       return []
#     end
#     cache[[n,k,min]] ||= begin
#       if k == 1
#         return [n]
#       end
#       (min..n-1).flat_map do |i|
#         combos(n-i,k-1, i, cache).map { |r| [i, *r] }
#       end
#     end
#   end

arr = [5,10,15,20,30]
ee = []
# max = 200
# while (ee.sum < max) do
  ee << arr.sample(1).first
# end

ee.pop(2)
val = max - ee.sum
pair = arr.uniq.combination(2).detect { |a, b| a + b == val }
ee << pair
ee.flatten

p ee