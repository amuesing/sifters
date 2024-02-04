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

        
    def normalize_waveform(self, waveform):
        normalized_waveform = numpy.int16(waveform / numpy.max(numpy.abs(waveform)) * 32767)
        return normalized_waveform


    def perform_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=5, synthesis_type='linear'):
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
            
            # Original FM waveform without ADSR envelope
            fm_wave = self.perform_fm_synthesis(enveloped_carrier, modulating_wave, synthesis_type=synthesis_type)

            enveloped_modulator = modulating_wave * modulator_envelopes[i]
            fm_wave_with_adsr = self.perform_fm_synthesis(enveloped_carrier, enveloped_modulator, synthesis_type=synthesis_type)

            # Superimposed plot for each grid
            matplotlib.pyplot.plot(fm_wave, label=f'Original FM Wave ({self.grids_set[i]} fraction)')
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