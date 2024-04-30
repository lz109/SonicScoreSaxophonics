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
interval = 0
m = 5
idx = 0
curr_time = 0
curr_notes_time = 0
curr_notes_idx = 0
ref_notes_time = 0
ref_notes_idx = 0
ref_fingering_time = 0
ref_fingering_idx = 0

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
    output_file_path = 'static/results/audio_output.txt'  # Adjust path as necessary

    with open(output_file_path, 'w') as file:
        file.write(output)
    return output


def load_data():
    global notes, fingerings
    notes = read_tuple_data('static/files/entire_range_notes.txt')
    fingerings = read_tuple_data('static/files/entire_range_fingerings.txt')

# later replace it, each time press start send a request to load the data
load_data()

# process_audio("static/audio/test.wav")

def home(request): 
    return render(request, "home.html") 
  
def learn(request): 
    return render(request, "learn.html") 

def practice(request):
    global index, currFingering, currNote, interval, m, idx, curr_time, curr_notes_time, curr_notes_idx, ref_notes_time, ref_notes_idx, ref_fingering_time, ref_fingering_idx
    index = -1
    currFingering = "00000000000000000000000"
    currNote = "notDetected"
    interval = 0
    m = 5
    idx = 0
    curr_time = 0
    curr_notes_time = 0
    curr_notes_idx = 0
    ref_notes_time = 0
    ref_notes_idx = 0
    ref_fingering_time = 0
    ref_fingering_idx = 0
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
    global interval, processed_notes, processed_fingering
    audio_path = 'static/results/audio_output.txt'
    processed_notes = read_tuple_data(audio_path)
    # for debug
    fingering_path = 'static/results/debug_fingering.txt'
    processed_fingering = read_line_data(fingering_path)
    total_time = sum(duration for note, duration in processed_notes)
    lines = len(processed_fingering)
    if lines == 0:
        return JsonResponse({'status': 'error', 'message': 'No fingering data'})
    interval = total_time / lines
    return JsonResponse({'status': 'success', 'message': 'interval', 'data': interval})

# get sync result, display as feedback
# TODO: implement
@csrf_exempt
def get_feedback(request):
    global notes, fingerings, processed_notes, processed_fingering, m, idx, curr_time, curr_notes_time, curr_notes_idx, ref_notes_time, ref_notes_idx, ref_fingering_time, ref_fingering_idx
    if idx >= len(processed_fingering):
        return JsonResponse({'status': 'error', 'message': 'No fingering data'})
    curr_fingering = processed_fingering[idx]
    curr_time += interval
    # problem to be solved: idx exceeds
    while(curr_notes_time < curr_time):
        if curr_notes_idx >= len(processed_notes):
            return JsonResponse({'status': 'error', 'message': 'No notes data'})
        curr_notes_time += processed_notes[curr_notes_idx][1]
        curr_notes_idx += 1
        print(curr_notes_time)
    curr_audio = processed_notes[curr_notes_idx-1][0]

    while(ref_notes_time < curr_time):
        if ref_notes_idx >= len(notes):
            return JsonResponse({'status': 'error', 'message': 'No ref notes data'})
        ref_notes_time += notes[ref_notes_idx][1]
        ref_notes_idx += 1
    ref_audio = notes[ref_notes_idx-1][0]

    while(ref_fingering_time < curr_time):
        if ref_fingering_idx >= len(fingerings):
            return JsonResponse({'status': 'error', 'message': 'No ref fingering data'})
        ref_fingering_time += fingerings[ref_fingering_idx][1]
        ref_fingering_idx += 1
    ref_fingering = fingerings[ref_fingering_idx-1][0]

    idx += 1

    # fix sharp issues
    if (curr_fingering == ref_fingering) and (curr_audio == ref_audio):
        m -= 1
        return JsonResponse({
        'status': 'success',
        'message': 'Current fingering and audio data',
        'data': {
            'current_fingering': curr_fingering,
            'current_audio': curr_audio,
            'ref_audio': ref_audio,
            'ref_fingering': ref_fingering
        }
    })
    m += 1
    if (m <= 5):
        return JsonResponse({
        'status': 'success',
        'message': 'Current fingering and audio data',
        'data': {
            'current_fingering': ref_fingering,
            'current_audio': ref_audio,
            'ref_audio': ref_audio,
            'ref_fingering': ref_fingering
        }
    })
    return JsonResponse({
        'status': 'success',
        'message': 'Current fingering and audio data',
        'data': {
            'current_fingering': curr_fingering,
            'current_audio': curr_audio,
            'ref_audio': ref_audio,
            'ref_fingering': ref_fingering
        }
    })