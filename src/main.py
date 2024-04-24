import argparse
import tensorflow as tf
import numpy as np
import model

def train_model():
  folder_path = 'data/midi_files/in'
  sequences = model.load_data(folder_path)

  x, y = model.prepare_sequences(sequences, sequence_length=100)

  midi_model = model.create_model(input_shape=(50, x.shape[2]), num_units=64, dropout_rate=0.3, num_classes=128)
  checkpoint = tf.keras.callbacks.ModelCheckpoint(filepath='data/model.h5', save_best_only=True, monitor='loss', mode='min')
  early_stopping = tf.keras.callbacks.EarlyStopping(monitor='loss', patience=5)
  midi_model.fit(x, y, epochs=50, batch_size=64, callbacks=[checkpoint, early_stopping])

  midi_model.save('data/model.h5')

def generate_music():
    generation_length = 100
    midi_model = tf.keras.models.load_model('data/model.h5')
    # Initialize seed_sequence with a suitable starting point
    seed_sequence = np.random.uniform(low=0, high=1, size=(100, 128))  # Example shape, adjust as needed

    generated_sequence = seed_sequence.copy()
    for _ in range(generation_length):
        next_note = midi_model.predict(seed_sequence[np.newaxis, :, :])
        next_note = next_note[0, -1, :]  # Assuming next_note is the last timestep of the prediction
        seed_sequence = np.vstack([seed_sequence[1:], next_note])

        generated_sequence = np.vstack([generated_sequence, next_note])

    # Assuming save_data expects a sequence of MIDI events
    model.save_data(generated_sequence, 'generated.mid')


def main():
  parser = argparse.ArgumentParser(description='Train a model to generate music')
  parser.add_argument('command', choices=['train', 'generate'], help='The command to run: train or generate')
  args = parser.parse_args()

  if args.command == 'train':
    train_model()
  elif args.command == 'generate':
    generate_music()

if __name__ == '__main__':
  main()