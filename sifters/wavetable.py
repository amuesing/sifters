import numpy
import scipy.io.wavfile
import matplotlib.pyplot


class Wavetable:
    
    
    def __init__(self, mediator):
        # Serum is optimized at 2048 cycles-per-frame
        self.num_samples = 2048
        # Serum is optimized at a sample rate of 96000
        self.sample_rate = 96000
        # 46.875 corresponds to the frequency of one cycle relative to the designated num_samples (2048) and sample_rate (96000)
        self.reference_frequency = 46.875
        self.time = numpy.arange(0, self.num_samples) / self.sample_rate
        
        self.grids_set = mediator.grids_set
    
    
    def generate_sine_wave(self, amplitude=1, frequency=None, time=None, phase=0):
        frequency = frequency if frequency is not None else self.reference_frequency
        time = time if time is not None else self.time

        sine_wave = amplitude * numpy.sin(2 * numpy.pi * frequency * time + phase)
        return sine_wave
    
    
    def generate_adsr_envelope(self, attack_time=.2, decay_time=.2, sustain_level=.75, release_time=.2, length=None):
        length = length if length is not None else self.num_samples
        envelope = numpy.zeros(length)
        
        # Attack
        attack_samples = int(attack_time * length)
        envelope[:attack_samples] = numpy.linspace(0, 1, attack_samples)
        
        # Decay
        decay_samples = int(decay_time * length)
        envelope[attack_samples:attack_samples + decay_samples] = numpy.linspace(1, sustain_level, decay_samples)
        
        # Sustain
        sustain_samples = length - attack_samples - decay_samples
        envelope[attack_samples + decay_samples:attack_samples + decay_samples + sustain_samples] = sustain_level
        
        # Release
        release_samples = int(release_time * length)
        envelope[-release_samples:] = numpy.linspace(sustain_level, 0, release_samples)
        
        return envelope
    
    
    def generate_carrier_wave(self, frequency_multiplier=16):
        carrier_frequency = self.reference_frequency * frequency_multiplier
        return self.generate_sine_wave(frequency=carrier_frequency)


    def generate_modulating_frequencies(self, frequency_multiplier=16):
        return [grid_fraction * self.reference_frequency * frequency_multiplier for grid_fraction in self.grids_set]


    def generate_carrier_envelope(self):
        return self.generate_adsr_envelope(attack_time=0.1, decay_time=0.4, sustain_level=0.8, release_time=0.1)


    def generate_modulator_envelopes(self):
        return [
            self.generate_adsr_envelope(attack_time=0.1, decay_time=0.4, sustain_level=0.55, release_time=0.2),
            self.generate_adsr_envelope(attack_time=0.15, decay_time=0.35, sustain_level=0.60, release_time=0.2),
            self.generate_adsr_envelope(attack_time=0.2, decay_time=0.3, sustain_level=0.65, release_time=0.2),
            self.generate_adsr_envelope(attack_time=0.25, decay_time=0.25, sustain_level=0.70, release_time=0.2),
            self.generate_adsr_envelope(attack_time=0.3, decay_time=0.2, sustain_level=0.75, release_time=0.2)
        ]
        
        
    def normalize_waveform(self, waveform):
        normalized_waveform = numpy.int16(waveform / numpy.max(numpy.abs(waveform)) * 32767)
        return normalized_waveform


    def perform_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=10, synthesis_type='linear'):
        if synthesis_type == 'linear':
            modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * modulation_index * modulating_signal * self.time)
        elif synthesis_type == 'exponential':
            modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * numpy.exp(modulation_index * modulating_signal) * self.time)
        else:
            raise ValueError("Invalid synthesis type. Use 'linear' or 'exponential'.")
        
        return self.normalize_waveform(modulated_signal)
    
    
    def visualize_fm_synthesis(self, modulating_frequencies, enveloped_carrier, modulator_envelopes, synthesis_type='linear'):
        for i, modulating_frequency in enumerate(modulating_frequencies):
            modulating_wave = self.generate_sine_wave(frequency=modulating_frequency)
            fm_wave = self.perform_fm_synthesis(enveloped_carrier, modulating_wave, synthesis_type=synthesis_type)

            enveloped_modulator = modulating_wave * modulator_envelopes[i]
            fm_wave_with_adsr = self.perform_fm_synthesis(enveloped_carrier, enveloped_modulator, synthesis_type=synthesis_type)

            matplotlib.pyplot.plot(fm_wave_with_adsr, label=f'FM Wave with ADSR ({self.grids_set[i]} fraction)')

        matplotlib.pyplot.title(f'FM Synthesis with Unique ADSR Envelopes ({synthesis_type.capitalize()} Synthesis)')
        matplotlib.pyplot.xlabel('Sample')
        matplotlib.pyplot.ylabel('Amplitude')
        matplotlib.pyplot.legend()
        matplotlib.pyplot.show()


    def save_fm_waveforms(self, modulating_frequencies, enveloped_carrier, modulator_envelopes, synthesis_type='linear'):
        for i, modulating_frequency in enumerate(modulating_frequencies):
            modulating_wave = self.generate_sine_wave(frequency=modulating_frequency)

            enveloped_modulator = modulating_wave * modulator_envelopes[i]
            fm_wave_with_adsr = self.perform_fm_synthesis(enveloped_carrier, enveloped_modulator, synthesis_type=synthesis_type)

            scipy.io.wavfile.write(f'data/wav/fm_wave_{i + 1}_{synthesis_type}.wav', self.sample_rate, self.normalize_waveform(fm_wave_with_adsr))

        print(f"{synthesis_type.capitalize()} WAV files saved successfully.")


    def run_fm_synthesis(self, synthesis_type='linear'):
        carrier_wave = self.generate_carrier_wave()
        modulating_frequencies = self.generate_modulating_frequencies()
        carrier_envelope = self.generate_carrier_envelope()
        modulator_envelopes = self.generate_modulator_envelopes()

        enveloped_carrier = carrier_wave * carrier_envelope

        # Save the carrier wave as a WAV file
        scipy.io.wavfile.write(f'data/wav/carrier_wave_{synthesis_type}.wav', self.sample_rate, self.normalize_waveform(carrier_wave))

        # Visualize and save FM synthesis results
        self.visualize_fm_synthesis(modulating_frequencies, enveloped_carrier, modulator_envelopes, synthesis_type=synthesis_type)
        self.save_fm_waveforms(modulating_frequencies, enveloped_carrier, modulator_envelopes, synthesis_type=synthesis_type)
