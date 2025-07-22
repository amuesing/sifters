import numpy
import matplotlib.pyplot
import scipy.io.wavfile


class Wavetable:
    
    
    def __init__(self):
        # Serum is optimized at 2048 cycles-per-frame
        self.num_samples = 2048
        # Serum is optimized at a sample rate of 96000
        self.sample_rate = 96000
        # 46.875 corresponds to the frequency of one cycle relative to the designated num_samples (2048) and sample_rate (96000)
        self.reference_frequency = 46.875
        self.time = numpy.arange(0, self.num_samples) / self.sample_rate
    
    
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

    # Serum is optimized for a 32-bit architecture
    def normalize_waveform(self, waveform):
        # Calculate the maximum absolute value in the waveform
        max_abs_value = numpy.max(numpy.abs(waveform))
        
        # Normalize the waveform to the range [-1, 1]
        normalized_waveform = waveform / max_abs_value
        
        # Scale the normalized waveform to fit within the range of a 32-bit signed integer
        scaled_waveform = normalized_waveform * 2147483647
        
        # Convert the result to a NumPy array of 32-bit integers
        normalized_waveform_32bit = numpy.int32(scaled_waveform)
        
        return normalized_waveform_32bit


    def perform_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index, synthesis_type):
        if synthesis_type == 'linear':
            modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * modulation_index * modulating_signal * self.time)
        elif synthesis_type == 'exponential':
            modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * numpy.exp(modulation_index * modulating_signal) * self.time)
        else:
            raise ValueError("Invalid synthesis type. Use 'linear' or 'exponential'.")
        
        return self.normalize_waveform(modulated_signal)


    def visualize_envelopes(self, carrier_envelope, modulator_envelopes):
        num_samples = len(carrier_envelope)

        # Create a figure
        matplotlib.pyplot.figure(figsize=(12, 6))

        # Plot carrier envelope
        matplotlib.pyplot.plot(numpy.arange(num_samples), carrier_envelope, 'r-', label='Carrier Envelope')

        # Plot modulator envelopes
        for i, modulator_env in enumerate(modulator_envelopes):
            matplotlib.pyplot.plot(numpy.arange(num_samples), modulator_env, label=f'Modulator Envelope {i + 1}', linestyle='--')

        matplotlib.pyplot.title('Carrier and Modulator Envelopes')
        matplotlib.pyplot.xlabel('Time (samples)')
        matplotlib.pyplot.ylabel('Amplitude')
        # matplotlib.pyplot.legend()

        # Show the plot
        matplotlib.pyplot.show()
    
    
    def visualize_fm_synthesis(self, enveloped_carrier, modulating_frequencies, modulator_envelopes, modulation_index, synthesis_type):
        for i, modulating_frequency in enumerate(modulating_frequencies):
            modulating_wave = self.generate_sine_wave(frequency=modulating_frequency)
            
            enveloped_modulator = modulating_wave * modulator_envelopes[i]
            fm_wave_with_adsr = self.perform_fm_synthesis(enveloped_carrier, enveloped_modulator, modulation_index, synthesis_type)

            matplotlib.pyplot.plot(fm_wave_with_adsr, label=f'FM Wave with ADSR ({i + 1} fraction)')

        matplotlib.pyplot.title(f'FM Synthesis with Unique ADSR Envelopes ({synthesis_type.capitalize()} Synthesis)')
        matplotlib.pyplot.xlabel('Sample')
        matplotlib.pyplot.ylabel('Amplitude')
        # matplotlib.pyplot.legend()
        matplotlib.pyplot.show()


    def save_fm_waveforms(self, enveloped_carrier, modulating_frequencies, modulator_envelopes, modulation_index, synthesis_type):
        for i, modulating_frequency in enumerate(modulating_frequencies):
            modulating_wave = self.generate_sine_wave(frequency=modulating_frequency)

            enveloped_modulator = modulating_wave * modulator_envelopes[i]
            fm_wave_with_adsr = self.perform_fm_synthesis(enveloped_carrier, enveloped_modulator, modulation_index, synthesis_type)

            scipy.io.wavfile.write(f'data/wav/{synthesis_type.capitalize()}{i + 1}_Index{modulation_index}.wav', self.sample_rate, self.normalize_waveform(fm_wave_with_adsr))

        print(f"{len(modulating_frequencies)} {synthesis_type.capitalize()} WAV files saved successfully.")
        
        
