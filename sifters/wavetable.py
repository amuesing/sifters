import numpy as np
from scipy.io.wavfile import write

# Set the parameters for the wavetable
wavetable_size = 2048  # Number of samples in the wavetable
sample_rate = 44100  # Sample rate in Hz

# Define multiple frequencies for the sinusoidal components
frequencies = [440.0]  # Example frequencies in Hz

# Create sinusoidal components for each frequency
waveforms = [np.sin(2 * np.pi * freq * np.arange(wavetable_size) / sample_rate) for freq in frequencies]

# Interpolate between the waveforms to create the final wavetable
interp_fraction = np.arange(wavetable_size) / (wavetable_size - 1)
custom_wavetable = sum((1 - interp_fraction) * waveform for waveform in waveforms)

# Scale the values to 16-bit PCM format
custom_wavetable = np.int16(custom_wavetable / len(frequencies) * 32767)

# Save the custom wavetable as a WAV file
write('custom_wavetable.wav', sample_rate, custom_wavetable)
