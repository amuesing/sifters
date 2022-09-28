import 

midi.init()
default_id = midi.get_default_input_id()
midi_input = midi.Input(device_id=default_id)