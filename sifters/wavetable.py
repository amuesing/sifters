import numpy as np
from scipy.io.wavfile import write

class Wavetable:

    def __init__(self, mediator):
        self.grids_set = mediator.grids_set
        self.selected_cents_implied_zero = mediator.texture.selected_cents_implied_zero
        self.wavetable_size = 2048
        self.sample_rate = 44100
        frequency_of_A = 440.0
        frequency_of_middle_C = frequency_of_A * (2 ** (-9/12))
        self.reference_frequency = frequency_of_middle_C
        self.frequency_list = self.cents_to_frequency(self.reference_frequency, self.selected_cents_implied_zero)
        self.carrier_signal = self.generate_carrier_signal()
        self.modulator_signals = self.generate_modulator_signals()
        self.apply_fm_synthesis()

    def cents_to_frequency(self, reference_frequency, cents_list):
        return [round(reference_frequency * 2**(cents / 1200), 2) for cents in cents_list]

    def generate_carrier_signal(self):
        float_frequencies = [float(fraction) for fraction in self.grids_set]
        waveforms = [np.sin(2 * np.pi * freq * np.arange(self.wavetable_size) / self.sample_rate) for freq in float_frequencies]
        interp_fraction = np.arange(self.wavetable_size) / (self.wavetable_size - 1)
        carrier_signal = sum((1 - interp_fraction) * waveform for waveform in waveforms)
        carrier_signal = np.int16(carrier_signal / len(float_frequencies) * 32767)
        return carrier_signal

    def generate_modulator_signals(self, fixed_amplitude=0.8, fixed_phase_offset=0.0, fixed_frequency_offset=0.0):
        modulator_signals = []
        for freq in self.frequency_list:
            modulator_signal = fixed_amplitude * np.sin(2 * np.pi * (freq + fixed_frequency_offset) * np.arange(self.wavetable_size) / self.sample_rate + fixed_phase_offset)
            modulator_signals.append(modulator_signal)

        return modulator_signals

    def apply_fm_synthesis(self, modulation_index=2.5):
        modulation_waveform = sum(self.modulator_signals)
        modulated_signal = np.sin(2 * np.pi * modulation_index * modulation_waveform) * self.carrier_signal
        modulated_signal = np.int16(modulated_signal / np.max(np.abs(modulated_signal)) * 32767)
        write('data/wav/wavetable.wav', self.sample_rate, modulated_signal)
        return modulated_signal