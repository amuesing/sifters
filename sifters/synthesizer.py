import numpy
import fractions
from scipy.io.wavfile import write
import matplotlib.pyplot as plt


class Synthesizer:
    
    def __init__(self, mediator):
        self.num_samples = 2048
        self.sample_rate = 96000
        
        # 46.875 cooresponds to the frequency of one cycle relative to the designated num_samples and sample_rate
        self.reference_frequency = 46.875
        self.time = numpy.arange(0, self.num_samples) / self.sample_rate
        
        self.grids_set = [fractions.Fraction(1, 40), fractions.Fraction(1, 20), fractions.Fraction(3, 40), fractions.Fraction(1, 10), fractions.Fraction(1, 8)]
        # self.grids_set = mediator.grids_set
    
    
    def generate_sine_wave(self, amplitude=1, frequency=None, time=None, phase=0):
        frequency = frequency if frequency is not None else self.reference_frequency
        time = time if time is not None else self.time

        sine_wave = amplitude * numpy.sin(2 * numpy.pi * frequency * time + phase)
        return sine_wave
    
    
    def generate_adsr_envelope(self, attack_time=.2, decay_time=.2, sustain_level=.75, release_time=.2, length=2048):
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


    def perform_linear_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=.01):
        modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * modulation_index * modulating_signal * self.time)
        return self.normalize_waveform(modulated_signal)
    
    
    def perform_exponential_fm_synthesis(self, carrier_signal, modulating_signal, modulation_index=0.01):
        modulated_signal = carrier_signal * numpy.sin(2 * numpy.pi * numpy.exp(modulation_index * modulating_signal) * self.time)
        return self.normalize_waveform(modulated_signal)
    
    
    def perform_additive_synthesis(self, frequencies, amplitudes):
        additive_wave = numpy.zeros(self.num_samples)
        for frequency, amplitude in zip(frequencies, amplitudes):
            harmonic_wave = self.generate_sine_wave(amplitude, frequency)
            additive_wave += harmonic_wave
        return additive_wave
    
    
    def normalize_waveform(self, waveform):
        normalized_waveform = numpy.int16(waveform / numpy.max(numpy.abs(waveform)) * 32767)
        return normalized_waveform
        
if __name__ == '__main__':
    synth = Synthesizer(mediator=None)

    # Use the reference frequency as the carrier frequency
    carrier_frequency = synth.reference_frequency * 64
    carrier_wave = synth.generate_sine_wave(frequency=carrier_frequency)
    
    # Use each grid fraction multiplied by the reference frequency as the modulating frequency
    modulating_frequencies = [grid_fraction * carrier_frequency for grid_fraction in synth.grids_set]
    
    envelope = synth.generate_adsr_envelope()
    
    enveloped_carrier = carrier_wave * envelope
    # Generate ADSR envelopes for each modulating frequency
    envelopes = [synth.generate_adsr_envelope() for _ in modulating_frequencies]

    # Perform FM synthesis for each modulating frequency and visualize the resulting waveforms
    for i, modulating_frequency in enumerate(modulating_frequencies):
        modulating_wave = synth.generate_sine_wave(frequency=modulating_frequency)
        enveloped_modulator = modulating_wave * envelope
        fm_wave = synth.perform_linear_fm_synthesis(carrier_wave, modulating_wave)

        # Visualize the waveform with FM synthesis and ADSR envelope
        plt.plot(fm_wave, label=f'FM Wave with ADSR ({synth.grids_set[i]} fraction)')
    
    plt.title('FM Synthesis with ADSR Envelopes')
    plt.xlabel('Sample')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.show()

    # Save the resulting waveforms with FM synthesis and ADSR envelope as WAV files
    for i, modulating_frequency in enumerate(modulating_frequencies):
        modulating_wave = synth.generate_sine_wave(frequency=modulating_frequency)
        fm_wave = synth.perform_linear_fm_synthesis(synth.generate_sine_wave(frequency=carrier_frequency),
                                                    modulating_wave)
        fm_wave_with_adsr = fm_wave * envelopes[i]

        # Save the waveform with FM synthesis and ADSR envelope as a WAV file
        write(f'data/wav/fm_wave_with_adsr_{i + 1}.wav', synth.sample_rate, synth.normalize_waveform(fm_wave_with_adsr))
    
    print("WAV files saved successfully.")
