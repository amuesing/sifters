rep = 4
i = 1


for _ in range(rep):
    y = i/2
    print(y)
    i += 1
    
def find_lcm(modulo):
    # check if *every* element in a list is a list
    if all(isinstance(i, list) for i in modulo):
        multiples = []
        for mod in modulo:
            multiples.append(np.lcm.reduce(mod))
        # find_lcm(multiples)
        return find_lcm(multiples)
    else:
        return np.lcm.reduce(modulo)
    