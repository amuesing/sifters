p (1..5).map { (("a".."z").to_a + [" "] * 10)[rand(36)] }.join