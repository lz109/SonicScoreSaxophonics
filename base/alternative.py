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

    return filtered_notes


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
