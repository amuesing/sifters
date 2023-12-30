import numpy

class Waveform:
    def __init__(self):
        self.num_samples = 2048
        self.sample_rate = 96000
        self.reference_frequency = 46.875
        self.time = numpy.arange(0, self.num_samples) / self.sample_rate
        
        
    def generate_sine_wave(self, amplitude=1, frequency=None, time=None, phase=0):
        frequency = frequency if frequency is not None else self.reference_frequency
        time = time if time is not None else self.time

        sine_wave = amplitude * numpy.sin(2 * numpy.pi * frequency * time + phase)
        return sine_wave