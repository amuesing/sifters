require 'midilib'
require 'midilib/io/seqreader'

# Create a new, empty sequence.
seq = MIDI::Sequence.new()

# Read the contents of a MIDI file into the sequence.
File.open('simple melody.mid', 'rb') { | file | seq.read(file) }

events = []

events = seq.map do |track|
  track.map { |e| e }
end