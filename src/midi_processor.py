import pretty_midi
import numpy as np
from cc_mappings import cc_mappings

def import_midi(file_path):
  midi_data = pretty_midi.PrettyMIDI(file_path)

  sequence = create_sequence_array(midi_data)

  for instrument in midi_data.instruments:
    process_midi_notes(sequence, instrument.notes)
    process_midi_pitch_bends(sequence, instrument.pitch_bends)
    process_midi_control_changes(sequence, instrument.control_changes)

  return sequence

def export_midi(sequence, filename):
  # TODO: Research to see what resolutions are commonly used
  resolution = 220.0
  latest_tick_duration = sequence[0]['tick_duration']
  initial_tempo = 60.0 / (latest_tick_duration * resolution)
  midi_data = pretty_midi.PrettyMIDI(initial_tempo=initial_tempo, resolution=resolution)
  program = pretty_midi.instrument_name_to_program('Organ')
  instrument = pretty_midi.Instrument(program=program)

  incomplete_notes = []
  for tick in sequence:
    process_sequence_notes(tick, instrument, incomplete_notes)
    process_sequence_pitch_bends(tick, instrument)
    process_sequence_control_changes(tick, instrument)
    # TODO: Adopt time signature into the midi file
    # process_sequence_tempo_changes(tick, midi_data)

  midi_data.instruments.append(instrument)
  midi_data.write('data/midi_files/out' + filename)

# TODO: Implement uuids for notes so they can be paired when exporting
def process_sequence_notes(tick, instrument, incomplete_notes):
  for note_event in tick['note_events']:
    unnorm_pitch = note_event['pitch'] * 127
    unnorm_velocity = note_event['velocity'] * 127

    if note_event['type'] == 'note_start':
      incomplete_note = {
        'pitch': unnorm_pitch,
        'velocity': unnorm_velocity,
        'start': tick['time']
      }
      incomplete_notes.append(incomplete_note)
    elif note_event['type'] == 'note_end':
      for note in incomplete_notes:
        if unnorm_pitch == note['pitch'] and unnorm_velocity == note['velocity']:
          new_note = pretty_midi.Note(
            velocity=int(unnorm_velocity),
            pitch=int(unnorm_pitch),
            start=note['start'],
            end=tick['time']
          )
          instrument.notes.append(note)
          incomplete_notes.remove(note)

def process_sequence_pitch_bends(tick, instrument):
  for pitch_bend_event in tick['pitch_bend_events']:
    # norm_bend = ((2.0 * (bend.pitch + 8192.0)) / 16383.0) - 1.0
    unnorm_bend = ((pitch_bend_event['value'] + 1.0) * 8191.5) - 8192.0
    new_bend = pretty_midi.PitchBend(
      pitch=int(unnorm_bend),
      time=tick['time']
    )
    instrument.pitch_bends.append(new_bend)

def process_sequence_control_changes(tick, instrument):
  for control_change_event in tick['control_change_events']:
    cc_mapping = find_mapping(0, control_change_event['number'])
    if not cc_mapping:
      continue

    if cc_mapping.type.value == 'continuous':
      low, high = cc_mapping.range
      range = high - low
      if low < 0:
        zero_adjust = 0 - low
        unnorm_value = ((control_change_event['value'] + 1.0) / 2.0) * range - zero_adjust
      else:
        unnorm_value = control_change_event['value'] * range + low
    elif cc_mapping.type.value == 'boolean':
      unnorm_value = 127 if control_change_event['value'] else 0
    elif cc_mapping.type.value == 'category':
      cc_option = find_option(cc_mapping, control_change_event['value'])
      unnorm_value = cc_option.midi_value

    new_cc = pretty_midi.ControlChange(
      number=control_change_event['number'],
      value=int(unnorm_value),
      time=tick['time']
    )
    instrument.control_changes.append(new_cc)

def create_sequence_array(midi_data):
  sequence = []
  tpqn = midi_data.resolution
  tempo_change_times, tempi = midi_data.get_tempo_changes()
  total_duration = midi_data.get_end_time()
  tempo_change_times = np.append(tempo_change_times, total_duration)

  last_tempo_change_time = 0.0
  tick_index = 0
  for i in range(len(tempo_change_times)):
    if i == len(tempo_change_times) - 1:
      break

    current_tempo = tempi[i]
    segment_start_time = last_tempo_change_time
    segment_end_time = tempo_change_times[i]
    segment_duration = segment_end_time - segment_start_time
    last_tempo_change_time = segment_end_time

    tick_duration = 60.0 / (current_tempo * tpqn)
    ticks_in_segment = int(np.floor(segment_duration / tick_duration))

    for tick in range(ticks_in_segment):
      absolute_time = segment_start_time + tick * tick_duration
      new_tick = create_tick(tick_index, tick_duration, absolute_time)
      sequence.append(new_tick)
      tick_index += 1

  if last_tempo_change_time < total_duration:
    remaining_ticks = int(np.floor((total_duration - last_tempo_change_time) / tick_duration))
    for tick in range(remaining_ticks):
      absolute_time = last_tempo_change_time + tick * tick_duration
      new_tick = create_tick(tick_index, tick_duration, absolute_time)
      sequence.append(new_tick)
      tick_index += 1

  return sequence

def create_tick(tick_index, tick_duration, absolute_time):
  return {
    'tick': tick_index,
    'tick_duration': tick_duration,
    'time': absolute_time,
    'note_events': [],
    'pitch_bend_events': [],
    'control_change_events': []
  }

# TODO: Create a uuid for each note so they can be paired when exporting
def process_midi_notes(sequence, midi_notes):
  notes = []
  for note in midi_notes:
    norm_pitch = note.pitch / 127.0
    norm_velocity = note.velocity / 127.0
    insert_note_event(sequence, note.start, 'note_start', norm_pitch, norm_velocity)
    insert_note_event(sequence, note.end, 'note_end', norm_pitch, norm_velocity)

def process_midi_pitch_bends(sequence, midi_pitch_bends):
  pitch_bends = []
  for bend in midi_pitch_bends:
    norm_bend = ((bend.pitch + 8192.0) / 8191.5) - 1.0
    insert_pitch_bend_event(sequence, bend.time, norm_bend)

def process_midi_control_changes(sequence, midi_control_changes):
  control_changes = []
  for change in midi_control_changes:
    # TODO: Handle multiple instruments
    cc_mapping = find_mapping(0, change.number)
    if not cc_mapping:
      continue

    norm_value = change.value / 127.0
    if cc_mapping.type.value == 'continuous':
      low, high = cc_mapping.range
      range = high - low
      if low < 0:
        zero_adjust = 0 - low
        norm_value = ((2.0 * (change.value + zero_adjust)) / range) - 1.0
      else:
        norm_value = (change.value - low) / range
    elif cc_mapping.type.value == 'boolean':
      if change.value == 0:
        norm_value = False
      else:
        norm_value = True
    elif cc_mapping.type.value == 'category':
      cc_option = find_option(cc_mapping, change.value)
      norm_value = cc_option.value
    
    # TODO: Handle multiple instruments
    insert_control_change_event(sequence, change.time, 0, change.number, norm_value)

def insert_note_event(sequence, time, event_type, pitch, velocity):
  e = {
    'type': event_type,
    'pitch': pitch,
    'velocity': velocity
  }
 
  sequence_tick = find_tick(sequence, time)
  if sequence_tick:
    sequence_tick['note_events'].append(e)
    
def insert_pitch_bend_event(sequence, time, value):
  e = {
    'type': 'pitch_bend_change',
    'value': value
  }

  sequence_tick = find_tick(sequence, time)
  if sequence_tick:
    sequence_tick['pitch_bend_events'].append(e)

def insert_control_change_event(sequence, time, instrument, number, value):
  e = {
    'type': 'control_change',
    'instrument': instrument,
    'number': number,
    'value': value
  }

  sequence_tick = find_tick(sequence, time)
  if sequence_tick:
    sequence_tick['control_change_events'].append(e)

# TODO: Improve this to go faster
#   We may need to use a different data structure to make this faster
def find_tick(sequence, time):
  low, high = 0, len(sequence) - 1
  while low <= high:
    mid = (low + high) // 2
    mid_time = sequence[mid]['time']
    if mid_time < time:
      low = mid + 1
    else:
      high = mid
      
    mid_duration = sequence[mid]['tick_duration']
    if time >= mid_time and time < mid_time + mid_duration:
      return sequence[mid]

  return None

def find_mapping(instrument, number):
  return next(
    (cc for cc in cc_mappings
      if cc.instrument == instrument and cc.number == number
    ),
    None
  )

def find_option(mapping, value):
  return next(
    (option for option in mapping.options
      if option.midi_value == value
    ),
    None
  )