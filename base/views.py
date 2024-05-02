from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.shortcuts import HttpResponseRedirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import json
import subprocess
import wave
import math
from django.conf import settings
from .models import CustomUser
from pydub import AudioSegment

  

notes = []
fingerings = []
processed_notes = []
processed_fingering = []
index = -1
currFingering = "00000000000000000000000"
currNote = "notDetected"

inc = False
interval = 0.5
curr_time = 0
offset = 0
tolerance = 0.5
idx = 0
duration = 0

def read_tuple_data(file_path):
    audio_data = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                note, duration = line.strip().split(',')
                audio_data.append((note, float(duration)))
    return audio_data

def read_line_data(file_path):
    fingerings = []
    with open(file_path, 'r') as file:
        for line in file:
            cleaned_line = line.strip()
            if cleaned_line:
                fingerings.append(cleaned_line)
    return fingerings

# process the audio with a .wav file
def process_audio(file):
    script_path = 'static/audioDetection/Demo.py'
    result = subprocess.run(['python', script_path, file], capture_output=True, text=True)
    integrated_audio = result.stdout.splitlines()[0]
    output = ""
    for s in integrated_audio:
        if s == "[" or s == "]" or s == "'" or s == " ":
            continue
        elif s == ":":
            output += ","
        elif s == ",":
            output += "\n"
        else:
            output += s
    output_file_path = 'static/results/audio_output.txt'

    with open(output_file_path, 'w') as file:
        file.write(output)
    return output

@csrf_exempt
def load_data(request):
    global notes, fingerings
    name = request.body.decode('utf-8')
    file_note_name = 'static/files/' + name + '_notes.txt'
    file_fingering_name = 'static/files/' + name + '_fingerings.txt'
    notes = read_tuple_data(file_note_name)
    fingerings = read_tuple_data(file_fingering_name)
    return JsonResponse({})

# process_audio("static/audio/test.wav")
notes = read_tuple_data('static/files/entire_range_notes.txt')
fingerings = read_tuple_data('static/files/entire_range_fingerings.txt')

def reset():
    global fingerings, processed_notes, processed_fingering, inc, interval, curr_time, offset, tolerance, idx, duration
    fingerings = read_tuple_data('static/files/entire_range_fingerings.txt')
    processed_notes = []
    processed_fingering = []
    inc = False
    interval = 0.5
    curr_time = 0
    offset = 0
    tolerance = 0.5
    idx = 0
    duration = 0

def home(request): 
    return render(request, "home.html") 
  
def learn(request): 
    return render(request, "learn.html") 

def practice(request):
    reset()
    return render(request, "practice.html")

@csrf_exempt
def practice_update(request):
    global index, currFingering, currNote

    if request.method == 'GET':
        if (index < 0):
            note = "start"
            fingering = "start"
        else:
            if (index >= len(notes)):
                note = "end"
                fingering = "end"
            else:
                note = notes[index][0]
                fingering = fingerings[index][0]
        return JsonResponse({
            'refNote': note,
            'refFingering': fingering,
            'currNote': currNote,  
            'currFingering': currFingering,  
        })
    
    elif request.method == 'POST':
        currFingering = request.POST.get('fingering')
        currNote = request.POST.get('note')

        return JsonResponse({})

def statistics(request): 
    if request.user.is_authenticated:
        customUser = get_object_or_404(CustomUser, userId=request.user.id)
        practice_count = customUser.practice_count
        total_practice_count = customUser.total_practice_count
        context = {'practice_count': practice_count, "total_practice_count": total_practice_count}
        return render(request, "statistics.html", context)
    return render(request, "statistics.html")

def audio_processing(request):
    file_path = "static/audio/recording.wav"
    try:
        # Process the audio file
        result = process_audio(file_path)
        return JsonResponse({'status': 'success', 'result': result})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def signup(request):
    if request.user.is_authenticated:
        return redirect('/learn')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            CustomUser.objects.create(userId=user.id)
            login(request, user)
            return redirect('/learn')
        else:
            return render(request, 'signup.html', {'form': form})
    else:
        form = UserCreationForm()
        return render(request, 'signup.html', {'form': form})
    
def signin(request):
    if request.user.is_authenticated:
        return redirect('/learn')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/learn')
        else:
            msg = 'Error Login'
            form = AuthenticationForm(request.POST)
            return render(request, 'login.html', {'form': form, 'msg': msg})
    else:
        form = AuthenticationForm()
        return render(request, 'login.html', {'form': form})
    
def signout(request):
    logout(request)
    return redirect('/')

@csrf_exempt
def periodic_update_entire_range(request):
    global index, currFingering, currNote
    
    index += 1
    if request.method == 'POST':
        index = -1
        currFingering = "00000000000000000000000"
        currNote = "notDetected"
        if request.user.is_authenticated:
            customUser = get_object_or_404(CustomUser, userId=request.user.id)
            customUser.practice_count += 1
            customUser.total_practice_count += 1
            customUser.save()

    if (index < 0):
        note = "start"
        fingering = "start"
        nextUp = "NextUp: " + notes[index+1][0]
    else:
        if (index >= len(notes)):
            note = "end"
            fingering = "end"
            nextUp = "The end of Practice"
        else:
            note = notes[index][0]
            fingering = fingerings[index][0]
            nextUp = "NextUp: " + notes[index+1][0] if index < len(notes) - 1 else "The end of Practice"
    
    return JsonResponse({
        'refNote': note,
        'refFingering': fingering,
        'next': nextUp
    })

@csrf_exempt
def upload_audio(request):
    if request.method == 'POST':
        audio_file = request.FILES.get('audio')
        if audio_file:
            handle_audio_file(audio_file)
            return JsonResponse({'status': 'success', 'message': 'Audio uploaded successfully'})
    return JsonResponse({'status': 'error', 'message': 'An error occurred'})

def handle_audio_file(f):
    with open('static/audio/recording.mp3', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    sound = AudioSegment.from_file('static/audio/recording.mp3')
    sound.export('static/audio/recording.wav', format="wav")

@csrf_exempt
def upload_fingering(request):
    if request.method == 'POST':
        content = request.body.decode('utf-8')
        with open('static/results/fingering_output.txt', 'w') as file:
            file.write(content)
        return JsonResponse({'status': 'success', 'message': 'Fingering file created successfully'})
    else:
        return JsonResponse({'status': 'error', 'message': 'An error occurred'})


# integrate audio_output.txt, fingering_output.txt, ref audio and ref fingering, store the sync results as a list or in a file
# TODO: implement
@csrf_exempt
def integration(request):
    global duration, processed_notes, processed_fingering, offset, inc, curr_time, offset, idx
    inc = False
    curr_time = 0
    offset = 0
    idx = 0

    # for debug
    audio_path = 'static/results/audio_output.txt'
    processed_notes = read_tuple_data(audio_path)
    # for debug
    fingering_path = 'static/results/fingering_output.txt'
    processed_fingering = read_line_data(fingering_path)
    total_time = sum(duration for note, duration in processed_notes)
    lines = len(processed_fingering)
    if lines == 0:
        return JsonResponse({'status': 'error', 'message': 'No fingering data'})
    duration = total_time / lines

    i = 0
    while(len(processed_fingering[i]) != 23 or processed_fingering[i] == "00000000000000000000000"):
        i += 1
        offset += duration

    # if processed_notes[0][0] == "R":
    #     curr_notes_idx += 1
    #     idx += math.ceil(processed_notes[0][1] / interval)
    #     print(idx)
    # print(i, offset)

    return JsonResponse({'status': 'success', 'message': 'interval', 'data': 0.5})

def is_note_equal(note1, note2):
    # Direct comparison if they are exactly the same
    if note1 == note2:
        return True
    
    # Create a mapping of notes to their immediate higher and lower notes
    scale = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B']
    # Find indices in the scale
    index1 = scale.index(note1[:-1])  # remove the octave for matching
    index2 = scale.index(note2[:-1])  # remove the octave for matching
    
    # Check adjacent notes, considering octave changes
    octave_diff = int(note1[-1]) - int(note2[-1])
    if octave_diff == 0 and abs(index1 - index2) == 1:  # same octave, adjacent notes
        return True
    elif octave_diff != 0:
        # Check for boundary cases (e.g., B3 and C4)
        if (note1[:-1] == 'B' and note2[:-1] == 'C' and octave_diff == -1) or \
           (note1[:-1] == 'C' and note2[:-1] == 'B' and octave_diff == 1):
            return True
    return False

# get sync result, display as feedback
# TODO: implement
@csrf_exempt
def get_feedback(request):
    global inc, interval, curr_time, offset, tolerance, idx, duration

    # 60%
    filtered_notes = find_notes_with_minimum_duration(processed_notes, offset + curr_time - tolerance, offset + interval + curr_time + tolerance, 0.3)
    # print(idx, offset + curr_time - tolerance, offset + interval + curr_time + tolerance, filtered_notes)

    # 60%
    filtered_fingering = filter_and_sort_fingerings(processed_fingering, offset + curr_time - tolerance, offset + interval + curr_time + tolerance, duration)
    # print(idx, offset + curr_time - tolerance, offset + interval + curr_time + tolerance, filtered_fingering)

    if idx >= len(fingerings):
        return JsonResponse({'status': 'error', 'message': 'No fingering data'})
    # every 0.5 sec
    ref_fingering = fingerings[idx][0]
    ref_audio = notes[idx][0]
    curr_fingering = "00000000000000000000000"
    curr_audio = "R"

    curr_time += 0.5
    if (not inc): inc = True
    elif (inc): 
        idx += 1
        inc = False

    if ref_fingering in filtered_fingering:
        curr_fingering = ref_fingering
    else: 
        if len(filtered_fingering) != 0:
            curr_fingering = filtered_fingering[0]

    for note in filtered_notes:
        if (is_note_equal(note, ref_audio)):
            curr_audio = ref_audio
    if (curr_audio == "R"):
        if len(filtered_notes) != 0:
            curr_audio = filtered_notes[0]
    
        
    return JsonResponse({
        'status': 'success',
        'message': 'Current fingering and audio data',
        'data': {
            'current_fingering': curr_fingering,
            'current_audio': curr_audio,
            'ref_audio': ref_audio,
            'ref_fingering': ref_fingering
        }})
    
    
    
def find_notes_with_minimum_duration(notes, start, end, min_duration):
    # Calculate start and end times for each note
    times = []
    current_time = 0
    for note, duration in notes:
        times.append((note, current_time, current_time + duration))
        current_time += duration

    # Calculate active durations for each note in the window
    note_durations = {}
    for note, note_start, note_end in times:
        if note_end > start and note_start < end:
            # Calculate overlapping duration
            overlap_start = max(start, note_start)
            overlap_end = min(end, note_end)
            overlap_duration = overlap_end - overlap_start
            if overlap_duration > 0:
                if note in note_durations:
                    note_durations[note] += overlap_duration
                else:
                    note_durations[note] = overlap_duration

    # Filter notes that have a duration >= min_duration and sort them
    filtered_notes = [(note, duration) for note, duration in note_durations.items() if duration >= min_duration]
    filtered_notes.sort(key=lambda x: x[1], reverse=True)

    sorted_notes = [note for note, _ in filtered_notes]

    return sorted_notes


def filter_and_sort_fingerings(fingerings, start, end, x):
    current_time = 0
    fingering_durations = []
    added_fingerings = set()  # Set to keep track of added fingerings to avoid duplicates

    # Iterate over each fingering with its duration
    for fingering in fingerings:
        # Calculate the start and end time for each fingering
        fingering_start = current_time
        fingering_end = current_time + x

        # Update the current time for the next fingering
        current_time += x

        # Check if the fingering falls within the specified time window
        if fingering_end > start and fingering_start < end:
            # Calculate the overlap with the window
            overlap_start = max(start, fingering_start)
            overlap_end = min(end, fingering_end)
            overlap_duration = overlap_end - overlap_start

            # Check if the overlapping duration is at least 0.6x seconds and the fingering has not been added
            if overlap_duration >= 0.6 * x and fingering not in added_fingerings:
                fingering_durations.append((fingering, overlap_duration))
                added_fingerings.add(fingering)  # Add fingering to the set to avoid future duplicates

    # Sort the list of tuples by the overlap duration in descending order
    fingering_durations.sort(key=lambda x: x[1], reverse=True)

    # Extract sorted fingerings from the list of tuples
    sorted_fingerings = [fingering for fingering, _ in fingering_durations]

    return sorted_fingerings



