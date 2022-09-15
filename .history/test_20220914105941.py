row = [1,2,3,4]

def generateSerialMatrix(row):
    interval = []
    columns = []
    matrix = []
    for tone in row:
        interval += (tone - row[0])
    print interval
        
        
generateSerialMatrix(row)