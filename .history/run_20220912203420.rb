Dir["../modules/*.rb"].each {|file| require file }
require "./serialisms/test.rb"

p combos(10,3)