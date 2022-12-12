from collections import defaultdict
import random

# https://douglasduhaime.com/posts/making-chiptunes-with-markov-models.html

# read the file
text = open('tests/shakespeare/tiny-shakespeare.txt').read()
# add START before each speech and END after
formatted = text.replace('\n\n', ' END \n\nSTART ')
# create the full training data string
training_data = 'START ' + formatted + ' END'

# split our training data into a list of words
words = training_data.split(' ')
# next_words will store the list of words that follow a word
next_words = defaultdict(list)
# examine each word up to but not including the last
for word_index, word in enumerate(words[:-1]):
  # indicate that the first word is followed by the next
  next_words[word].append( words[word_index+1] )
  # generate 100 samples from the model
for i in range(100):
  # initialize a string that will store our output
  output = ''
  # select a random word that follows START
  word = random.choice(next_words['START'])
  # continue selecting the next word until we hit the END marker
  while word != 'END':
    # add the current word to the output
    output += word + ' '
    # get the next word in the sequence
    word = random.choice(next_words[word])
  # display out the output
  print(output.strip(), '\n')