live_loop :setter do
    set :foo, rrand(70, 130)
    sleep 1
  end
  
  live_loop :getter do
    puts get[:foo]
    sleep 0.5
  end