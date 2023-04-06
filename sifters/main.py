from modules.generators import *

def main():
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    voices = {
        'mono1': texture.NonPitched(sivs),
        'mono2': texture.Monophonic(sivs, '4/3', form='Retrograde')
    }
    
    output = score.Score(**voices)
    # output.combine_parts('mono1', 'mono2')
    output.write_score()
    
if __name__ == '__main__':
    main()