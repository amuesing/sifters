import numpy
from scipy.io.wavfile import write
import matplotlib.pyplot as plt
from matplotlib import gridspec


class Wavetable:
    
    def __init__(self, mediator):
        self.num_samples = 2048
        self.sample_rate = 96000
        self.reference_frequency = 46.875
        self.time = numpy.arange(0, self.num_samples) / self.sample_rate
        
        # self.sine_wave = self.generate_sine_wave()
        # self.grids_set = mediator.grids_set
        # self.binary = mediator.binary
        # self.selected_cents_implied_zero = mediator.texture.selected_cents_implied_zero
        # self.frequency_list = [self.reference_frequency] + self.cents_to_frequency(self.reference_frequency, self.selected_cents_implied_zero)
        
    
    def visualize_waveforms(self, waveforms, titles=None, combined_title='Waveform Visualization'):
        num_waveforms = len(waveforms)
        num_cols = 1
        num_rows = num_waveforms

        # Use gridspec to create a flexible grid
        gs = gridspec.GridSpec(num_rows, num_cols, height_ratios=[1] * num_rows)

        plt.figure(figsize=(8, 6))

        for i, waveform in enumerate(waveforms):
            ax = plt.subplot(gs[i])
            ax.plot(self.time, waveform)
            ax.set_title(titles[i] if titles else f'Waveform {i + 1}')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude')
            ax.grid(True)
            ax.set_ylim([-1.1 * max(abs(waveform)), 1.1 * max(abs(waveform))])  # Adjust y-axis range

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
    
    # def generate_sine_wave(self, amplitude=.3, frequency=None, time=None, phase=0):
    #     frequency = frequency if frequency is not None else self.reference_frequency
    #     time = time if time is not None else self.time

    #     sine_wave = amplitude * numpy.sin(2 * numpy.pi * frequency * time + phase)
    #     return self.normalize_waveform(sine_wave)
    
    # def generate_sine_wave(self, phase_offset=0):
    #     sine_wave = numpy.sin(2 * numpy.pi * self.reference_frequency * self.time + phase_offset)
    #     return self.normalize_waveform(sine_wave)
    
    
    # def generate_sawtooth_wave(self):
    #     sawtooth_wave = numpy.mod(self.time * self.reference_frequency, 1)
    #     return self.normalize_waveform(sawtooth_wave)


    # def generate_square_wave(self):
    #     square_wave = numpy.sign(numpy.sin(2 * numpy.pi * self.frequency * self.time))
    #     return self.normalize_waveform(square_wave)


    # def generate_triangle_wave(self):
    #     triangle_wave = 2 * numpy.abs(numpy.mod(self.time * self.frequency, 1) - 0.5) - 0.5
    #     return self.normalize_waveform(triangle_wave)
    
    
    def generate_sine_wave(self, amplitude=1, frequency=None, time=None, phase=0):
        frequency = frequency if frequency is not None else self.reference_frequency
        time = time if time is not None else self.time

        sine_wave = amplitude * numpy.sin(2 * numpy.pi * frequency * time + phase)
        return sine_wave


    def perform_linear_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=0.1):
        modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * modulation_index * modulating_signal * self.time)
        return self.normalize_waveform(modulated_signal)
    
    
    def perform_exponential_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=0.01):
        modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * numpy.exp(modulation_index * modulating_signal * self.time))
        return self.normalize_waveform(modulated_signal)
    
    
    def perform_additive_synthesis(self, frequencies, amplitudes):
        additive_wave = numpy.zeros(self.num_samples)
        for frequency, amplitude in zip(frequencies, amplitudes):
            harmonic_wave = self.generate_sine_wave(amplitude, frequency)
            additive_wave += harmonic_wave
        return additive_wave


if __name__ == '__main__':
    wave = Wavetable(mediator=None)

    frequencies = [46.875, 55.74, 59.75, 60.79, 71.05, 72.29, 77.48]
    amplitudes = [1, .1, .1, .1, .1, .1, .1]

    # Generate individual sine waves
    individual_waves = [wave.generate_sine_wave(amplitude, frequency) for amplitude, frequency in zip(amplitudes, frequencies)]

    # Perform and save additive synthesis step by step
    for i in range(len(frequencies)):
        partial_sum_waveform = wave.perform_additive_synthesis(frequencies[:i+1], amplitudes[:i+1])
        normalized_partial_sum_waveform = wave.normalize_waveform(partial_sum_waveform)

        # Save the partial sum waveform as a WAV file
        write(f'data/wav/partial_sum_step_{i+1}.wav', wave.sample_rate, normalized_partial_sum_waveform)

    # # Visualize the final additive synthesis waveform
    # additive_waveform = wave.perform_additive_synthesis(frequencies, amplitudes)
    # normalized_additive_waveform = wave.normalize_waveform(additive_waveform)

    # # Visualize individual sine waves and the final additive synthesis waveform on the same graph
    # wave_titles = [f'Sine Wave {i+1}' for i in range(len(individual_waves))]

    # wave.visualize_waveforms(individual_waves, titles=wave_titles, combined_title='Individual Sine Waves')