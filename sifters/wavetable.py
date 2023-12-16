import numpy
from scipy.io.wavfile import write

class Wavetable:
    
    def __init__(self):
    # def __init__(self, mediator):
        # self.grids_set = mediator.grids_set
        # self.selected_cents_implied_zero = mediator.texture.selected_cents_implied_zero
        self.sample_rate = 96000
        self.reference_frequency = 46.875
        self.num_samples = 2048
        self.time = numpy.arange(0, self.num_samples) / self.sample_rate
        # self.frequency_list = self.cents_to_frequency(self.reference_frequency, self.selected_cents_implied_zero)

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
    
    def generate_square_wave(self, frequency):
        square_wave = numpy.sign(numpy.sin(2 * numpy.pi * frequency * self.time))
        square_wave_normalized = numpy.int16(square_wave * 32767)
        return square_wave_normalized

    def generate_triangle_wave(self, frequency):
        triangle_wave = 2 * numpy.abs(numpy.mod(self.time * frequency, 1) - 0.5) - 0.5
        triangle_wave_normalized = numpy.int16(triangle_wave * 32767)
        return triangle_wave_normalized

    def perform_linear_sine_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=0.1):
        modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * modulation_index * modulating_signal * self.time)
        modulated_signal_normalized = numpy.int16(modulated_signal / numpy.max(numpy.abs(modulated_signal)) * 32767)
        return modulated_signal_normalized
    
    def perform_exponential_sine_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=0.1):
        modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * numpy.exp(modulation_index * modulating_signal) * self.time)
        modulated_signal_normalized = numpy.int16(modulated_signal / numpy.max(numpy.abs(modulated_signal)) * 32767)
        return modulated_signal_normalized
    
    def perform_linear_square_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=0.1):
        modulated_signal = carrier_signal * numpy.sign(numpy.sin(2 * numpy.pi * modulating_signal * self.time + modulation_index * numpy.sin(2 * numpy.pi * modulating_signal * self.time)))
        modulated_signal_normalized = numpy.int16(modulated_signal / numpy.max(numpy.abs(modulated_signal)) * 32767)
        return modulated_signal_normalized
    
    def perform_exponential_square_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=0.1):
        modulated_signal = carrier_signal * numpy.sign(numpy.sin(2 * numpy.pi * modulating_signal * self.time + numpy.exp(modulation_index * numpy.sin(2 * numpy.pi * modulating_signal * self.time))))
        modulated_signal_normalized = numpy.int16(modulated_signal / numpy.max(numpy.abs(modulated_signal)) * 32767)
        return modulated_signal_normalized



if __name__ == '__main__':
    # Write methods for various modulation methods that combine multiple modulation frequencies such as Cascading and Parallel techniques
    fm_wave = Wavetable()
    
    sine_wave = fm_wave.generate_sine_wave(fm_wave.reference_frequency)
    write("data/wav/sine_wave.wav", fm_wave.sample_rate, sine_wave)
    
    sawtooth_wave = fm_wave.generate_sawtooth_wave(fm_wave.reference_frequency)
    write("data/wav/sawtooth_wave.wav", fm_wave.sample_rate, sawtooth_wave)
    
    # Additional waveform examples
    square_wave = fm_wave.generate_square_wave(fm_wave.reference_frequency)
    write("data/wav/square_wave.wav", fm_wave.sample_rate, square_wave)
    
    triangle_wave = fm_wave.generate_triangle_wave(fm_wave.reference_frequency)
    write("data/wav/triangle_wave.wav", fm_wave.sample_rate, triangle_wave)
    
    exponential_synthesis = fm_wave.perform_exponential_sine_fm_synthesis(sine_wave, sawtooth_wave)
    write("data/wav/exponential_synthesis.wav", fm_wave.sample_rate, exponential_synthesis)