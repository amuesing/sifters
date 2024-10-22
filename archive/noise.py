import numpy as np
from scipy.io.wavfile import write
from scipy.signal import lfilter, butter
import os

# Parameters
sample_rate = 44100
duration = 5
volume = 0.5
num_samples = sample_rate * duration

# Path to save WAV files
output_dir = 'data/wav'
os.makedirs(output_dir, exist_ok=True)

# Generate white noise for both channels
white_noise_left = np.random.uniform(-1, 1, num_samples)
white_noise_right = np.random.uniform(-1, 1, num_samples)

# Pink Noise
def generate_pink_noise(white_noise):
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1, -2.494956002, 2.017265875, -0.522189400]
    pink_noise = volume * lfilter(b, a, white_noise)
    return pink_noise

# Filtered Noise
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

def generate_filtered_noise(white_noise, lowcut, highcut):
    filtered_noise = volume * bandpass_filter(white_noise, lowcut, highcut, sample_rate)
    return filtered_noise

# Amplitude Modulated Noise
def generate_am_noise(white_noise, lfo_frequency):
    t = np.linspace(0, duration, num_samples, False)
    lfo = 0.5 * (1 + np.sin(2 * np.pi * lfo_frequency * t))
    am_noise = volume * white_noise * lfo
    return am_noise

# Create stereo signal with independent channels
def create_stereo_signal(mono_signal_left, mono_signal_right):
    return np.column_stack((mono_signal_left, mono_signal_right))

# Save as a WAV file
def save_wav(filename, signal):
    file_path = os.path.join(output_dir, filename)
    write(file_path, sample_rate, signal.astype(np.float32))
    print(f'Sample saved as {file_path}')

# Generate and save white noise
white_noise_stereo = create_stereo_signal(white_noise_left, white_noise_right)
save_wav('white_noise.wav', white_noise_stereo)

# Generate and save pink noise
pink_noise_left = generate_pink_noise(white_noise_left)
pink_noise_right = generate_pink_noise(white_noise_right)
pink_noise_stereo = create_stereo_signal(pink_noise_left, pink_noise_right)
save_wav('pink_noise.wav', pink_noise_stereo)

# Generate and save filtered noise
lowcut = 500.0  # 500 Hz
highcut = 5000.0  # 5000 Hz
filtered_noise_left = generate_filtered_noise(white_noise_left, lowcut, highcut)
filtered_noise_right = generate_filtered_noise(white_noise_right, lowcut, highcut)
filtered_noise_stereo = create_stereo_signal(filtered_noise_left, filtered_noise_right)
save_wav('filtered_noise.wav', filtered_noise_stereo)

# Generate and save amplitude modulated noise
lfo_frequency = 5.0  # 5 Hz
am_noise_left = generate_am_noise(white_noise_left, lfo_frequency)
am_noise_right = generate_am_noise(white_noise_right, lfo_frequency)
am_noise_stereo = create_stereo_signal(am_noise_left, am_noise_right)
save_wav('am_noise.wav', am_noise_stereo)

print('All noise samples generated and saved successfully.')
