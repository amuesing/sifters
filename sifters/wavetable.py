import numpy as np
from scipy.io.wavfile import write

class Wavetable:

    def __init__(self, mediator):
        self.grids_set = mediator.grids_set
        self.selected_cents_implied_zero = mediator.texture.selected_cents_implied_zero
        self.wavetable_size = 2048  # Number of samples in the wavetable
        self.sample_rate = 44100  # Sample rate in Hz
        # 261.63 is c4
        self.reference_frequency = 261.63
        self.frequency_list = self.cents_to_frequency(self.reference_frequency, self.selected_cents_implied_zero)
        print(self.frequency_list)
        # print(self.selected_cents_implied_zero)
        # Apply FM synthesis in the constructor
        self.modulated_signal = self.apply_fm_synthesis()
        
    def cents_to_frequency(self, reference_frequency, cents_list):
        # Convert each cent value to frequency using the formula
        frequency_list = [reference_frequency * 2**(cents / 1200) for cents in cents_list]
        return frequency_list


    def generate_carrier_signal(self):
        # Extract floating-point frequencies from Fraction objects
        float_frequencies = [float(fraction) for fraction in self.grids_set]

        # Create sinusoidal components for each frequency
        waveforms = [np.sin(2 * np.pi * freq * np.arange(self.wavetable_size) / self.sample_rate) for freq in float_frequencies]

        # Interpolate between the waveforms to create the final wavetable
        interp_fraction = np.arange(self.wavetable_size) / (self.wavetable_size - 1)
        carrier_signal = sum((1 - interp_fraction) * waveform for waveform in waveforms)

        # Scale the values to 16-bit PCM format
        carrier_signal = np.int16(carrier_signal / len(float_frequencies) * 32767)

        return carrier_signal


    def generate_modulator_signals(self):
        # Extract floating-point frequencies from Fraction objects for modulators
        modulator_frequencies = [float(fraction) for fraction in self.grids_set]

        # Create modulator signals with variations
        modulator_signals = []
        for freq in modulator_frequencies:
            amplitude = np.random.uniform(0.5, 1.0)  # Vary the amplitude
            phase_offset = np.random.uniform(0, 2 * np.pi)  # Vary the phase
            frequency_offset = np.random.uniform(-0.5, 0.5)  # Vary the frequency

            modulator_signal = amplitude * np.sin(2 * np.pi * (freq + frequency_offset) * np.arange(self.wavetable_size) / self.sample_rate + phase_offset)
            modulator_signals.append(modulator_signal)

        return modulator_signals



    def apply_fm_synthesis(self, modulation_index=2.5):
        # Generate the carrier signal
        self.carrier_signal = self.generate_carrier_signal()

        # Generate modulator signals
        modulator_signals = self.generate_modulator_signals()

        # Combine modulator signals to create modulation waveform
        modulation_waveform = sum(modulator_signals)

        # Apply FM synthesis to the carrier signal
        modulated_signal = np.sin(2 * np.pi * modulation_index * modulation_waveform) * self.carrier_signal

        # Scale the values to 16-bit PCM format
        modulated_signal = np.int16(modulated_signal / np.max(np.abs(modulated_signal)) * 32767)

        # Save the modulated signal as a WAV file
        write('data/wav/wavetable.wav', self.sample_rate, modulated_signal)

        return modulated_signal