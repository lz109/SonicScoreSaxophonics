import librosa
import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter
from scipy.signal import butter, sosfilt, sosfreqz
import sys
from scipy.fft import rfft, rfftfreq
import soundfile as sf

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
        if note is not None and note != 'R':
            midi_note = librosa.note_to_midi(note) + semitones
            transposed_note = librosa.midi_to_note(midi_note)
            transposed_notes.append(transposed_note)
        else:
            transposed_notes.append('R')
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
        if dominant_freq_db > db_threshold and dominant_freq > 70.0 and dominant_freq < 800:
            note = librosa.hz_to_note(dominant_freq)
            notes.append(note)
        else:
            notes.append('R')

        dominant_frequencies.append(dominant_freq)

    notes = transpose_notes(notes, semitones=2)

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
            if current_note is not None and note != current_note:
                # Append the previous note with its duration and start the new note
                integrated_notes.append(Note(current_note, round(note_duration, 1)))
                note_duration = 0  # Reset the duration for the new note
            current_note = note  # Set or update the current note
        # Always add the fraction duration as long as the current note is set
        if current_note is not None:
            note_duration += fraction_duration

    # Ensure the last note is added
    if current_note is not None and note_duration > 0:
        integrated_notes.append(Note(current_note, round(note_duration, 1)))

    return integrated_notes


'''def adjust_note_durations(notes):
    i = 0
    while i < len(notes):
        if notes[i].length < 0:
            if i > 0:  # there is a previous note
                notes[i - 1].length = round(notes[i - 1].length + notes[i].length / 2, 1)
            if i + 1 < len(notes):  # there is a next note
                notes[i + 1].length = round(notes[i + 1].length + notes[i].length / 2, 1)
            notes.pop(i)
        else:
            i += 1
    return notes'''


def plot_frequency_curve(frequencies, sr, hop_length):
    time_axis = np.arange(len(frequencies)) * (hop_length / sr)
    plt.plot(time_axis, frequencies)
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.title('Frequency Curve')
    plt.show()

def plot_spectrogram(audio_path):
    # Load the audio file
    y, sr = librosa.load(audio_path, sr=None)  # sr=None to preserve original sampling rate

    # Compute the Short-Time Fourier Transform (STFT)
    D = librosa.stft(y)
    
    # Convert amplitude to decibels
    D_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
    
    # Plot the spectrogram
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(D_db, sr=sr, x_axis='time', y_axis='log', cmap='coolwarm')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Spectrogram')
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.tight_layout()
    plt.show()


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
    y, sr = librosa.load(audio_path, sr = None)
    #y_slow = librosa.effects.time_stretch(y, rate=1)
    #sf.write('slowed_down_output.wav', y_slow, sr)
    #y = y_slow
    print("sr",sr)
    duration_in_seconds = len(y) / sr

    # Apply the band-pass filter
    lowcut = 20.0
    highcut = 4500.0
    #filtered_y = butter_bandpass_filter(y, lowcut, highcut, sr, order=6)
    filtered_y = y
 
    tempo, _ = librosa.beat.beat_track(y=filtered_y, sr=sr)
    eighth_note_duration = 60 / tempo / 8
    hop_length = int(eighth_note_duration * sr)
    print("tempo", tempo)
    print("hop", hop_length/sr)

    notes, frequencies = detect_pitch(filtered_y, sr, tempo)
    print("Array of Notes:", notes)

    rhythm_array, hop_length = detect_rhythm(filtered_y, sr, tempo)
    print("Rhythm Array:", rhythm_array)

    integrated_notes = integrate_notes(notes, rhythm_array, tempo, beat_fraction=8)
    #integrated_notes = adjust_note_durations(integrated_notes)
    print("result:", integrated_notes)

    plot_frequency_curve(frequencies, sr, hop_length)
    #plot_spectrogram('B_flat_2.wav')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("invalid")
        sys.exit(1)  # Exit the script with an error status

    audio_file = sys.argv[1]
    main(audio_file)