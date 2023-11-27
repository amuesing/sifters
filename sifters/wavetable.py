import numpy as np
from scipy.io.wavfile import write

class Wavetable:

    def __init__(self, mediator):
        self.grids_set = mediator.grids_set
        self.wavetable_size = 2048  # Number of samples in the wavetable
        self.sample_rate = 44100  # Sample rate in Hz

        # Generate and save the carrier signal
        self.carrier_signal = self.generate_fm_carrier_wavetable()

        # Apply FM synthesis in the constructor
        self.modulated_signal = self.apply_fm_synthesis()
        

    def generate_fm_carrier_wavetable(self):
        # Extract floating-point frequencies from Fraction objects
        float_frequencies = [float(fraction) for fraction in self.grids_set]

        # Create sinusoidal components for each frequency
        waveforms = [np.sin(2 * np.pi * freq * np.arange(self.wavetable_size) / self.sample_rate) for freq in float_frequencies]

        # Interpolate between the waveforms to create the final wavetable
        interp_fraction = np.arange(self.wavetable_size) / (self.wavetable_size - 1)
        carrier_signal = sum((1 - interp_fraction) * waveform for waveform in waveforms)

        # Scale the values to 16-bit PCM format
        carrier_signal = np.int16(carrier_signal / len(float_frequencies) * 32767)

        # Save the custom wavetable as a WAV file (optional)
        write('data/wav/wavetable.wav', self.sample_rate, carrier_signal)

        return carrier_signal
    
    
    def apply_fm_synthesis(self, modulation_index=1.333):
        # Extract floating-point frequencies from Fraction objects for modulators
        modulator_frequencies = [float(fraction) for fraction in self.grids_set]

        # Create modulator signals
        modulator_signals = [np.sin(2 * np.pi * freq * np.arange(self.wavetable_size) / self.sample_rate) for freq in modulator_frequencies]

        # Combine modulator signals to create modulation waveform
        modulation_waveform = sum(modulator_signals)

        # Apply FM synthesis to the carrier signal
        modulated_signal = np.sin(2 * np.pi * modulation_index * modulation_waveform) * self.carrier_signal

        # Scale the values to 16-bit PCM format
        modulated_signal = np.int16(modulated_signal / np.max(np.abs(modulated_signal)) * 32767)

        # Save the modulated signal as a WAV file (optional)
        write('data/wav/modulated_signal.wav', self.sample_rate, modulated_signal)

        return modulated_signal
