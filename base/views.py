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
from django.conf import settings
from .models import CustomUser
  

notes = []
fingerings = []
index = -1
currFingering = "00000000000000000000000"
currNote = "notDetected"

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
    # use two files to keep track of the notes and fingering, later can get the
    # song by parsing request, and then change the files this function reads
    with open("static/files/entire_range_notes.txt", 'r') as note_file:
        notes = note_file.read().splitlines()
    with open("static/files/entire_range_fingerings.txt", 'r') as fingering_file:
        fingerings = fingering_file.read().splitlines()

# later replace it, each time press start send a request to load the data
load_data()

# process_audio("static/audio/test.wav")

def home(request): 
    return render(request, "home.html") 
  
def learn(request): 
    return render(request, "learn.html") 

def practice(request):
    global index, currFingering, currNote
    index = -1
    currFingering = "00000000000000000000000"
    currNote = "notDetected"
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
                note = notes[index]
                fingering = fingerings[index]
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
    # later replace it with a file generated from request
    file_path = "static/audio/test.wav"
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
        nextUp = "NextUp: " + notes[index+1]
    else:
        if (index >= len(notes)):
            note = "end"
            fingering = "end"
            nextUp = "The end of Practice"
        else:
            note = notes[index]
            fingering = fingerings[index]
            nextUp = "NextUp: " + notes[index+1] if index < len(notes) - 1 else "The end of Practice"
    
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
            # Save the file or process it
            save_path = os.path.join(settings.BASE_DIR, 'static', 'audio', audio_file.name)
            handle_audio_file(audio_file)
            with open(save_path, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)
            return JsonResponse({'status': 'success', 'message': 'Audio uploaded successfully'})
    return JsonResponse({'status': 'error', 'message': 'An error occurred'})

def handle_audio_file(f):
    with open('static/audio/audio.mp3', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    


