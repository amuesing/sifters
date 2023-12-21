import numpy
from scipy.io.wavfile import write
import matplotlib.pyplot as plt
from matplotlib import gridspec


class Wavetable:
    
    def __init__(self, mediator):
        # self.grids_set = mediator.grids_set
        # self.binary = mediator.binary
        # self.selected_cents_implied_zero = mediator.texture.selected_cents_implied_zero
        # self.frequency_list = self.cents_to_frequency(self.reference_frequency, self.selected_cents_implied_zero)

        self.num_samples = 2048
        self.sample_rate = 96000
        self.reference_frequency = 46.875
        duration = 1.0
        self.time = numpy.arange(0, self.num_samples) / self.sample_rate
        
        self.sine_wave = self.generate_sine_wave
    
    
    def visualize_waveforms(self, waveforms, titles=None, combined_title='Waveform Visualization'):
        num_waveforms = len(waveforms)
        num_cols = 1
        num_rows = num_waveforms

        # Use gridspec to create a flexible grid
        gs = gridspec.GridSpec(num_rows, num_cols, height_ratios=[1] * num_rows)

        plt.figure(figsize=(8, 6))

        for i, waveform in enumerate(waveforms, 1):
            ax = plt.subplot(gs[i - 1])
            ax.plot(self.time, waveform)
            ax.set_title(titles[i - 1] if titles else f'Waveform {i}')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude')
            ax.grid(True)

        plt.suptitle(combined_title, y=1.02)
        plt.tight_layout()
        plt.show()
        
        
    def cents_to_frequency(self, reference_frequency, cents_list):
        return [round(reference_frequency * 2**(cents / 1200), 2) for cents in cents_list]

        
    def normalize_waveform(self, waveform):
        normalized_waveform = numpy.int16(waveform / numpy.max(numpy.abs(waveform)) * 32767)
        return normalized_waveform
    
    
    # def generate_sine_wave(self):
    #     sine_wave = numpy.sin(2 * numpy.pi * self.reference_frequency * self.time)
    #     return self.normalize_waveform(sine_wave)
    
    def generate_sine_wave_equal_parts(self, num_parts=1):
        phase_offsets = 2 * numpy.pi * numpy.arange(num_parts) / num_parts
        sine_wave = numpy.sin(2 * numpy.pi * self.reference_frequency * self.time + phase_offsets[:, numpy.newaxis])
        return self.normalize_waveform(numpy.sum(sine_wave, axis=0))
    
    def generate_sine_wave(self, phase_offset=0):
        sine_wave = numpy.sin(2 * numpy.pi * self.reference_frequency * self.time + phase_offset)
        return self.normalize_waveform(sine_wave)


    def generate_sawtooth_wave(self):
        sawtooth_wave = numpy.mod(self.time * self.reference_frequency, 1)
        return self.normalize_waveform(sawtooth_wave)


    def generate_square_wave(self):
        square_wave = numpy.sign(numpy.sin(2 * numpy.pi * self.frequency * self.time))
        return self.normalize_waveform(square_wave)


    def generate_triangle_wave(self):
        triangle_wave = 2 * numpy.abs(numpy.mod(self.time * self.frequency, 1) - 0.5) - 0.5
        return self.normalize_waveform(triangle_wave)


    def perform_linear_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=0.1):
        modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * modulation_index * modulating_signal * self.time)
        return self.normalize_waveform(modulated_signal)
    
    
    def perform_exponential_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=0.01):
        modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * numpy.exp(modulation_index * modulating_signal * self.time))
        return self.normalize_waveform(modulated_signal)


if __name__ == '__main__':
    # Write methods for various modulation methods that combine multiple modulation frequencies such as Cascading and Parallel techniques
    wave = Wavetable(mediator=None)
    
    # sine_wave = wave.generate_sine_wave()
    # write("data/wav/sine_wave.wav", wave.sample_rate, sine_wave)
    # wave.visualize_waveforms([sine_wave])
    
    # # Example binary sequence
    # binary_sequence = [0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0]
    # changes = [1, 1, 6, 1, 7, 1, 6, 1, 7, 1, 1, 1, 6]
    
    # sine_wave = wave.generate_sine_wave(phase_offset=numpy.pi/2)
    sine_wave = wave.generate_sine_wave_equal_parts(2)

    write("data/wav/sine_wave.wav", wave.sample_rate, sine_wave)
    wave.visualize_waveforms([sine_wave])

