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
    
    
    def generate_sine_wave(self):
        sine_wave = numpy.sin(2 * numpy.pi * self.reference_frequency * self.time)
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


    def perform_linear_sine_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=0.1):
        modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * modulation_index * modulating_signal * self.time)
        return self.normalize_waveform(modulated_signal)


    def perform_linear_square_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=0.1):
        modulated_signal = carrier_signal * numpy.sign(numpy.sin(2 * numpy.pi * modulating_signal * self.time + modulation_index * numpy.sin(2 * numpy.pi * modulating_signal * self.time)))
        return self.normalize_waveform(modulated_signal)
    
    
    def perform_exponential_sine_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=0.01):
        modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * numpy.exp(modulation_index * modulating_signal * self.time))
        return self.normalize_waveform(modulated_signal)
    
    
    def perform_pwm_on_sine_wave(self, duty_cycle=0.5, modulation_frequency=5.0):
        """
        Perform Pulse Width Modulation (PWM) on a sine wave.

        Parameters:
        - duty_cycle (float): The duty cycle of the PWM signal (default is 0.5).
        - modulation_frequency (float): The frequency of the modulating signal (default is 5.0).

        Returns:
        - numpy.ndarray: The PWM-modulated sine wave.
        """
        # Generate a modulating signal (square wave) with the specified duty cycle and frequency
        modulating_signal = numpy.mod(self.time * modulation_frequency, 1) < duty_cycle

        # Generate a sine wave
        sine_wave = self.generate_sine_wave()

        # Apply PWM by multiplying the sine wave with the modulating signal
        pwm_wave = sine_wave * modulating_signal

        return self.normalize_waveform(pwm_wave)
    

if __name__ == '__main__':
    # Write methods for various modulation methods that combine multiple modulation frequencies such as Cascading and Parallel techniques
    wave = Wavetable(mediator=None)
    
    sine_wave = wave.generate_sine_wave()
    write("data/wav/sine_wave.wav", wave.sample_rate, sine_wave)
    # wave.visualize_waveform(sine_wave)
    
    # sawtooth_wave = wave.generate_sawtooth_wave()
    # write("data/wav/sawtooth_wave.wav", wave.sample_rate, sawtooth_wave)
    # # wave.visualize_waveform(sawtooth_wave)
    
    # linear_synthesis = wave.perform_linear_sine_fm_synthesis(sine_wave, sawtooth_wave)
    # write("data/wav/linear_synthesis.wav", wave.sample_rate, linear_synthesis)
    
        
    # exponential_synthesis = wave.perform_exponential_sine_fm_synthesis(sine_wave, sawtooth_wave)
    # write("data/wav/exponential_synthesis.wav", wave.sample_rate, exponential_synthesis)

    # wave.visualize_waveforms([sine_wave, sawtooth_wave, exponential_synthesis],
    #                          titles=['Sine Wave', 'Sawtooth Wave', 'Exponential Synthesis'],
    #                          combined_title='Combined Waveforms')
    
    # # Additional waveform examples
    # square_wave = wave.generate_square_wave(wave.reference_frequency)
    # write("data/wav/square_wave.wav", wave.sample_rate, square_wave)
    
    # triangle_wave = wave.generate_triangle_wave(wave.reference_frequency)
    # write("data/wav/triangle_wave.wav", wave.sample_rate, triangle_wave)
    
    # Example usage of the PWM method
    pwm_sine_wave = wave.perform_pwm_on_sine_wave(duty_cycle=0.3, modulation_frequency=2.0)
    write("data/wav/pwm_sine_wave.wav", wave.sample_rate, pwm_sine_wave)

    wave.visualize_waveforms([sine_wave, pwm_sine_wave],
                         titles=['Sine Wave', 'PWM Sine Wave'],
                         combined_title='Combined Waveforms')
    

    
    # Example binary sequence
    binary_sequence = [0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0]
    changes = [1, 1, 6, 1, 7, 1, 6, 1, 7, 1, 1, 1, 6]
