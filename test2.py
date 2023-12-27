import numpy as np
import matplotlib.pyplot as plt

class SineWaveGenerator:
    def __init__(self, num_samples, sample_rate, reference_frequency):
        self.num_samples = num_samples
        self.sample_rate = sample_rate
        self.reference_frequency = reference_frequency

    def generate_sine_wave(self):
        t = np.arange(self.num_samples) / self.sample_rate
        frequency = self.reference_frequency
        sine_wave = np.sin(2 * np.pi * frequency * t)
        return t, sine_wave

    def apply_hann_window(self, signal):
        hann_window = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(self.num_samples) / (self.num_samples - 1))
        return signal * hann_window

    def generate_and_plot_sine_wave_with_envelope(self):
        t, sine_wave = self.generate_sine_wave()
        enveloped_wave = self.apply_hann_window(sine_wave)

        # Plot original and enveloped wave
        plt.plot(t, sine_wave, label='Original Sine Wave')
        plt.plot(t, enveloped_wave, label='Enveloped Sine Wave')
        plt.title('Sine Wave with Hann Window Envelope')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Amplitude')
        plt.legend()
        plt.show()

# Instantiate the SineWaveGenerator with your specified values
generator = SineWaveGenerator(num_samples=2048, sample_rate=96000, reference_frequency=46.875)

# Generate and plot the sine wave with Hann window envelope
generator.generate_and_plot_sine_wave_with_envelope()
