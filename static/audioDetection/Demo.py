import librosa
import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter
from scipy.signal import butter, sosfilt, sosfreqz
import sys

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

'''def detect_pitch(y_filtered, sr, tempo):
    eighth_note_duration = 60 / tempo / 8
    hop_length = int(eighth_note_duration * sr)  # Convert duration to number of samples

    # Iterate using the sliding window
    notes = []
    frequencies = []  
    for i in range(0, len(y_filtered) - hop_length, hop_length):
        window = y_filtered[i:i + hop_length]
        D = librosa.stft(window)

        magnitude = np.abs(D)
        max_freq_index = np.argmax(magnitude, axis=0)
        freqs = librosa.fft_frequencies(sr=sr)
        pitch = freqs[max_freq_index]

        # Convert pitch to music note
        note = librosa.hz_to_note(pitch[0])
        notes.append(note)
        frequencies.append(pitch[0])
    transposed_notes = transpose_notes(notes)
        
    return transposed_notes, frequencies'''

def detect_pitch(y, sr, tempo):
    # Calculate hop length as 1/8th of a beat
    beat_duration = 60 / tempo  # Duration of a beat in seconds
    eighth_note_duration = beat_duration / 8  # Duration of 1/8th of a beat
    hop_length = int(sr * eighth_note_duration)  # Convert to samples

    '''interval_duration = 0.125  # 1/8th of a beat
    hop_length = int(interval_duration * sr)'''
    
    # Compute STFT
    D = librosa.stft(y, hop_length=hop_length, n_fft=2048)
    magnitude = np.abs(D)
    
    # Find frequencies with maximum magnitude in each frame
    max_freq_indices = np.argmax(magnitude, axis=0)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    pitches = freqs[max_freq_indices]

    # Filter out non-positive frequencies
    valid_pitches = pitches[(pitches > 50) & (pitches < 1500)]
    
    # Convert valid pitches to music notes
    notes = [librosa.hz_to_note(pitch) for pitch in valid_pitches]
    transposed_notes = transpose_notes(notes)
    
    return transposed_notes, valid_pitches

def detect_rhythm(y, sr, tempo):
    eighth_note_duration = 60 / tempo / 8
    hop_length = int(eighth_note_duration * sr)

    '''interval_duration = 0.125  # 1/8th of a beat
    hop_length = int(interval_duration * sr)'''
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


def integrate_notes(noteList, beatList):
    integrated_notes = {}
    current_note = None
    note_duration = 0

    for note, beat in zip(noteList, beatList):
        if beat == 1:
            if current_note:
                integrated_notes[current_note] = integrated_notes.get(current_note, 0) + note_duration
            current_note = note
            note_duration = 1/8  # New note, reset duration to 1/8
        else:
            # Note is held, increase its duration
            note_duration += 1/8

    if current_note:
        integrated_notes[current_note] = integrated_notes.get(current_note, 0) + note_duration

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
    # print("Array of Notes:", notes)

    rhythm_array, hop_length = detect_rhythm(filtered_y, sr, tempo)
    # print("Rhythm Array:", rhythm_array)

    integrated_notes = integrate_notes(notes, rhythm_array)
    print(integrated_notes)

    # plot_frequency_curve(frequencies, sr, hop_length)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <path_to_audio_file>")
        sys.exit(1)  # Exit the script with an error status

    audio_file = sys.argv[1]
    main(audio_file)