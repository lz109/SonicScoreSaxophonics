import requests
import time

# simulate user input
def send_request_to_django():
    url = 'http://127.0.0.1:8000/practice/update'

    with open('tests/testNote.txt', 'r') as file:
        notes = file.read().splitlines()
    
    with open('tests/testFingering.txt', 'r') as file:
        fingerings = file.read().splitlines()
    
    time.sleep(2)
    for note, fingering in zip(notes, fingerings):
        data = {'fingering': fingering, 'note': note}
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        
        time.sleep(1.5)

send_request_to_django()