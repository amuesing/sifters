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

class Note
    attr_accessor :position, :note, :length
  
    def initialize(position, note, length)
      @position = position
      @note = note
      @length = length
    end
    
    def to_s
      "#{@position}, #{@note}, #{@length}"
    end
  end

  quarter_note_length = seq.note_to_delta('quarter')

notes = []

events.first.each do |event|
  if event.kind_of?(MIDI::NoteOn)
    note = Note.new(event.time_from_start, event.note, quarter_note_length)
    notes << note
  end
end
