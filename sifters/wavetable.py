import numpy
from scipy.io.wavfile import write

class Wavetable:

    def __init__(self, mediator):
        self.grids_set = mediator.grids_set
        self.selected_cents_implied_zero = mediator.texture.selected_cents_implied_zero
        self.sample_rate = 96000
        self.reference_frequency = 46.875
        self.num_samples = 2048
        self.modulation_index = .1
        self.time = numpy.arange(0, self.num_samples) / self.sample_rate
        self.frequency_list = self.cents_to_frequency(self.reference_frequency, self.selected_cents_implied_zero)
        self.carrier_signal = self.generate_sine_wave(self.reference_frequency)
        self.modulating_signal = self.generate_sawtooth_wave(self.reference_frequency)
        self.modulated_signal = self.perform_linear_fm_synthesis(self.carrier_signal, self.modulating_signal, self.modulation_index)

        write("data/wav/carrier_signal.wav", self.sample_rate, self.carrier_signal)
        write("data/wav/modulating_signal.wav", self.sample_rate, self.modulating_signal)
        write("data/wav/modulated_signal.wav", self.sample_rate, self.modulated_signal)

    def cents_to_frequency(self, reference_frequency, cents_list):
        return [round(reference_frequency * 2**(cents / 1200), 2) for cents in cents_list]

    def generate_sine_wave(self, frequency):
        sine_wave = numpy.sin(2 * numpy.pi * frequency * self.time)
        sine_wave_normalized = numpy.int16(sine_wave * 32767)
        return sine_wave_normalized

    def generate_sawtooth_wave(self, frequency):
        sawtooth_wave = numpy.mod(self.time * frequency, 1)
        sawtooth_wave_normalized = numpy.int16(sawtooth_wave * 32767)
        return sawtooth_wave_normalized

    def perform_linear_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index):
        modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * modulation_index * modulating_signal * self.time)
        modulated_signal_normalized = numpy.int16(modulated_signal / numpy.max(numpy.abs(modulated_signal)) * 32767)
        return modulated_signal_normalized
