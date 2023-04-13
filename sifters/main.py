from modules.generators import *

def main():
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    # sivs = '((5@0|5@1|5@4)&(3@1|3@2))', '((5@0|5@1|3@2)&3@0)'
    voices = {
        'np1': texture.NonPitched(sivs),
        'np2': texture.NonPitched(sivs, '4/3'),
        'np3': texture.NonPitched(sivs, '4/5'),
        'mono1': texture.Monophonic(sivs),
    }
    
    output = score.Score(**voices)
    # Why is .combine_parts not working with voices of different Classes?
    output.combine_parts('np1', 'np2', 'np3', 'mono1')
    output.write_score()
    
if __name__ == '__main__':
    main()