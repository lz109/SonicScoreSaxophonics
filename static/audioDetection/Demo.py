import librosa
import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter
from scipy.signal import butter, sosfilt, sosfreqz
import sys
from scipy.fft import rfft, rfftfreq

def preprocess_audio_with_snr_check(audio_path):
    y, sr = librosa.load(audio_path)
    
    snr = calculate_snr(y)
    if snr < 60:  # 60 dB threshold 
        return None, None 
    
    # Normalization & Filtering 
    y = y / np.max(np.abs(y))
    sos = butter(10, 100, btype='highpass', fs=sr, output='sos')
    filtered_audio = lfilter(sos, y)
    
    return filtered_audio, sr

def calculate_snr(signal):
    return 60  

def butter_bandpass(lowcut, highcut, sr, order=5):
    nyq = 0.5 * sr
    low = lowcut / nyq
    high = highcut / nyq
    sos = butter(order, [low, high], analog=False, btype='band', output='sos')
    return sos

def butter_bandpass_filter(data, lowcut, highcut, sr, order=5):
    sos = butter_bandpass(lowcut, highcut, sr, order=order)
    y = sosfilt(sos, data)
    return y

def transpose_notes(notes, semitones=2):
    transposed_notes = []
    for note in notes:
        if note is not None:
            midi_note = librosa.note_to_midi(note) + semitones
            transposed_note = librosa.midi_to_note(midi_note)
            transposed_notes.append(transposed_note)
        else:
            transposed_notes.append(None)
    return transposed_notes

def detect_pitch(data, sr, tempo):
    # Calculate the duration of 1/8th of a beat in seconds
    beat_duration = 60 / tempo  # Full beat duration in seconds
    eighth_note_duration = beat_duration / 8

    # Calculate the number of samples per 1/8th of a beat
    samples_per_eighth_note = int(sr * eighth_note_duration)

    notes = []
    spectrogram_data = []
    dominant_frequencies = []

    # Process each 1/8th beat segment
    for start in range(0, len(data), samples_per_eighth_note):
        end = start + samples_per_eighth_note
        data_slice = data[start:end]

        # Pad the last segment if necessary
        if len(data_slice) < samples_per_eighth_note:
            data_slice = np.pad(data_slice, (0, samples_per_eighth_note - len(data_slice)), mode='constant')

        # Apply a window to the slice
        window = np.hanning(len(data_slice))
        data_windowed = data_slice * window

        # Fourier Transform
        yf = rfft(data_windowed)
        xf = rfftfreq(len(data_windowed), 1 / sr)

        # Calculate dB levels of the frequency components
        yf_db = 20 * np.log10(np.abs(yf) + 1e-6)

        # Append absolute values to spectrogram data (for visualization, if needed)
        spectrogram_data.append(yf_db)

        # Get the most dominant frequency
        idx = np.argmax(np.abs(yf))
        dominant_freq = xf[idx]
        dominant_freq_db = yf_db[idx]
        db_threshold = 20
        # Filter and convert frequency to music note if above the dB threshold and significantly above zero
        if dominant_freq_db > db_threshold and dominant_freq > 90.0 and dominant_freq < 700:
            note = librosa.hz_to_note(dominant_freq)
            notes.append(note)
            dominant_frequencies.append(dominant_freq)

    return notes, dominant_frequencies

def detect_rhythm(y, sr, tempo):
    eighth_note_duration = 60 / tempo / 8
    hop_length = int(eighth_note_duration * sr)

    rhythm_array = []
    # Iterate through the signal with sliding window
    for i in range(0, len(y) - hop_length, hop_length):
        window = y[i:i + hop_length]
        peaks, _ = find_peaks(window)
        if len(peaks) > 0:
            # Append 1 if peak detected, indicating new note
            rhythm_array.append(1)
        else:
            rhythm_array.append(0)
    return rhythm_array, hop_length

class Note:
    def __init__(self, pitch, length):
        self.pitch = pitch
        self.length = length

    def __repr__(self):
        return f"{self.pitch}:{self.length}"

def integrate_notes(noteList, beatList, tempo, beat_fraction=8):
    beat_duration = 60 / tempo  # Full beat duration in seconds
    fraction_duration = beat_duration / beat_fraction

    integrated_notes = []
    current_note = None
    note_duration = 0
    previous_note = None  # To track if the same note is played sequentially

    for note, beat in zip(noteList, beatList):
        if beat == 1:
            if (current_note != None):
                current_note = note
                if current_note == previous_note:
                    note_duration += fraction_duration
                else:
                    # A new note starts, append the previous note and reset duration
                    integrated_notes.append(Note(current_note, round(note_duration, 1)))
                    current_note = note
                    note_duration = fraction_duration
            else:
                # This is the first note
                current_note = note
                note_duration = fraction_duration
        else: #beat==0
            # Note is held, increase its duration
            note_duration += fraction_duration

        previous_note = current_note  # Update the previous note

    # Append the last note after the loop ends
    if current_note:
        if current_note == previous_note:
            # Add the last note's duration to the last element if it's the same note
            integrated_notes[-1].length += round(note_duration, 1)
        else:
            integrated_notes.append(Note(current_note, round(note_duration, 1)))

    return integrated_notes


def plot_frequency_curve(frequencies, sr, hop_length):
    time_axis = np.arange(len(frequencies)) * (hop_length / sr)
    plt.plot(time_axis, frequencies)
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.title('Frequency Curve')
    plt.show()

def load_and_trim_audio(audio_path, sr=None, trim_start_sec=0.5):
    # Load the audio file
    y, sr = librosa.load(audio_path, sr=sr)
    trim_samples = int(trim_start_sec * sr)
    # Trim the start of the audio
    y_trimmed = y[trim_samples:]
    
    return y_trimmed, sr

def preprocess_and_threshold_audio(y, threshold_ratio=0.1, sr=None):
    # Load the audio file
    y_normalized = y / np.max(np.abs(y))
    
    threshold = threshold_ratio * np.max(np.abs(y_normalized))
    
    y_thresholded = np.copy(y_normalized)
    below_threshold_indices = np.abs(y_normalized) < threshold
    y_thresholded[below_threshold_indices] *= 0  # Scale down by 50%
    
    return y_thresholded

def main(audio_path):
    '''audio, sr = preprocess_audio_with_snr_check(audio_path)
    if audio is None:
        print("Audio does not meet SNR requirements.")
        return'''
    #y, sr=load_and_trim_audio(audio_path)
    #y, sr = preprocess_and_threshold_audio(audio_path)
    y, sr = librosa.load(audio_path, sr = 22050)

    # Apply the band-pass filter
    lowcut = 20.0
    highcut = 4500.0
    filtered_y = butter_bandpass_filter(y, lowcut, highcut, sr, order=6)
    #filtered_y = y
 
    tempo, _ = librosa.beat.beat_track(y=filtered_y, sr=sr)

    notes, frequencies = detect_pitch(filtered_y, sr, tempo)
    #print("Array of Notes:", notes)

    rhythm_array, hop_length = detect_rhythm(filtered_y, sr, tempo)
    #print("Rhythm Array:", rhythm_array)

    integrated_notes = integrate_notes(notes, rhythm_array, tempo, beat_fraction=8)
    print(integrated_notes)

    #plot_frequency_curve(frequencies, sr, hop_length)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <path_to_audio_file>")
        sys.exit(1)  # Exit the script with an error status

    audio_file = sys.argv[1]
    main(audio_file)