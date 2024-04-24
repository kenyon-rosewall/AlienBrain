import tensorflow as tf
import numpy as np
import midi_processor as mp
import os

def load_data(folder_path):
  sequences = []
  for filename in os.listdir(folder_path):
    if filename.endswith(".mid"):
      file_path = os.path.join(folder_path, filename)
      try:
        sequence = mp.import_midi(file_path)
        sequences.append(sequence)
      except Exception as e:
        print(f"Failed to process {filename}: {e}")

  return sequences

def save_data(sequence, filename):
  mp.export_midi(sequence, filename)

def create_model(input_shape, num_units=64, dropout_rate=0.3, num_classes=128):
  model = tf.keras.Sequential([
      tf.keras.layers.LSTM(num_units, input_shape=input_shape, return_sequences=True),
      tf.keras.layers.Dropout(dropout_rate),
      tf.keras.layers.LSTM(num_units),
      tf.keras.layers.Dropout(dropout_rate),
      tf.keras.layers.Dense(num_classes, activation='softmax')
  ])
  model.compile(optimizer='adam', loss='categorical_crossentropy')
  return model

def prepare_sequences(sequences, sequence_length):
  x = []
  y = []
  for sequence in sequences:
    for i in range(len(sequence) - sequence_length):
      input_sequence = sequence[i:i+sequence_length]
      output_sequence = sequence[i+sequence_length]
      x.append(input_sequence)
      y.append(output_sequence)

  return np.array(x), np.array(y)
