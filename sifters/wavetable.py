import numpy
from scipy.io.wavfile import write

class Wavetable:
    
    def __init__(self, mediator):
        self.grids_set = mediator.grids_set
        self.selected_cents_implied_zero = mediator.texture.selected_cents_implied_zero
        self.sample_rate = 96000
        self.reference_frequency = 46.875
        self.num_samples = 2048
        self.frequency_list = self.cents_to_frequency(self.reference_frequency, self.selected_cents_implied_zero)
        self.carrier_signal = self.generate_carrier_signal()
        
        modulating_signal = self.generate_modulating_signal(self.reference_frequency, 1.0)
        modulated_signal = self.perform_fm_synthesis(self.carrier_signal, modulating_signal)

        write("data/wav/carrier_signal.wav", self.sample_rate, self.carrier_signal)
        write("data/wav/modulating_signal.wav", self.sample_rate, modulating_signal)
        write("data/wav/modulated_signal.wav", self.sample_rate, modulated_signal)

    def cents_to_frequency(self, reference_frequency, cents_list):
        return [round(reference_frequency * 2**(cents / 1200), 2) for cents in cents_list]

    def generate_carrier_signal(self):
        t = numpy.arange(0, self.num_samples) / self.sample_rate
        sine_wave = numpy.sin(2 * numpy.pi * self.reference_frequency * t)
        sine_wave_normalized = numpy.int16(sine_wave * 32767)
        carrier_signal = sine_wave_normalized
        return carrier_signal

    def generate_modulating_signal(self, modulation_frequency, modulation_depth):
        t_modulation = numpy.arange(0, self.num_samples) / self.sample_rate
        sawtooth_wave = numpy.mod(t_modulation * modulation_frequency, 1)
        modulating_signal = numpy.int16((1.0 + modulation_depth * sawtooth_wave) * 32767)
        return modulating_signal

    def perform_fm_synthesis(self, carrier_signal, modulating_signal):
        modulated_signal = carrier_signal * modulating_signal
        modulated_signal_normalized = numpy.int16(modulated_signal / numpy.max(numpy.abs(modulated_signal)) * 32767)
        return modulated_signal_normalized