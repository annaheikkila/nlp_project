''
from __future__ import print_function
import string

from keras.models import Model
from keras.layers import Input, LSTM, Dense, Embedding
import numpy as np

batch_size = 64  # Batch size for training.
epochs = 80  # Number of epochs to train for.
latent_dim = 25  # Latent dimensionality of the encoding space.
num_samples = 12000  # Number of samples to train on.
# Path to the data txt file on disk.
data_path = 'swe.txt'

# Vectorize the data.
input_texts = []
target_texts = []
input_characters = set()
target_characters = set()

with open(data_path, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')
for line in lines[: len(lines) - 1]: #we input the sentences in an uuugly way, so we need to read the whole file
    target_text, input_text = line.split('\t')

    # translator for removing punctuation
    translator = str.maketrans('', '', string.punctuation)

    # read wordbased instead of charbased and make all words lowercase without punktuation
    input_text = input_text.lower().translate(translator).split(' ')
    target_text = target_text.lower().translate(translator).split(' ')
    # We use "tab" as the "start sequence" word
    # for the targets, and "\n" as "end sequence" word.
    target_text = ['\t'] + target_text + ['\n']
    input_texts.append(input_text)
    target_texts.append(target_text)
    for char in input_text:
        if char not in input_characters:
            input_characters.add(char)
    for char in target_text:
        if char not in target_characters:
            target_characters.add(char)

input_characters = sorted(list(input_characters))
target_characters = sorted(list(target_characters))
num_encoder_tokens = len(input_characters)
num_decoder_tokens = len(target_characters)
max_encoder_seq_length = max([len(txt) for txt in input_texts])
max_decoder_seq_length = max([len(txt) for txt in target_texts])

print('Number of samples:', num_samples)
print('Number of unique input tokens:', num_encoder_tokens)
print('Number of unique output tokens:', num_decoder_tokens)
print('Max sequence length for inputs:', max_encoder_seq_length)
print('Max sequence length for outputs:', max_decoder_seq_length)

input_token_index = dict(
    [(char, i) for i, char in enumerate(input_characters)])
target_token_index = dict(
    [(char, i) for i, char in enumerate(target_characters)])

encoder_input_data = np.zeros(
    (len(input_texts), max_encoder_seq_length, num_encoder_tokens),
    dtype='float32')
decoder_input_data = np.zeros(
    (len(input_texts), max_decoder_seq_length, num_decoder_tokens),
    dtype='float32')
decoder_target_data = np.zeros(
    (len(input_texts), max_decoder_seq_length, num_decoder_tokens),
    dtype='float32')


for i, (input_text, target_text) in enumerate(zip(input_texts, target_texts)):
    for t, word in enumerate(input_text):
        encoder_input_data[i, t, input_token_index[word]] = 1.
    for t, word in enumerate(target_text):
        # decoder_target_data is ahead of decoder_input_data by one timestep
        decoder_input_data[i, t, target_token_index[word]] = 1.
        if t > 0:
            # decoder_target_data will be ahead by one timestep
            # and will not include the start character.
            decoder_target_data[i, t - 1, target_token_index[word]] = 1.

# Define an input sequence and process it.
encoder_inputs = Input(shape=(None, ))
embedded_encoder_input = Embedding(num_encoder_tokens, 20)(encoder_inputs)
encoder = LSTM(latent_dim, return_state=True)
encoder_outputs, state_h, state_c = encoder(embedded_encoder_input)
# We discard `encoder_outputs` and only keep the states.
encoder_states = [state_h, state_c]

# Set up the decoder, using `encoder_states` as initial state.
decoder_inputs = Input(shape=(None, ))
embedded_decoder_input = Embedding(num_decoder_tokens, 20)(decoder_inputs)
# We set up our decoder to return full output sequences,
# and to return internal states as well. We don't use the
# return states in the training model, but we will use them in inference.
decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True)
decoder_outputs, _, _ = decoder_lstm(embedded_decoder_input,
                                     initial_state=encoder_states)
decoder_dense = Dense(num_decoder_tokens, activation='softmax')
decoder_outputs = decoder_dense(decoder_outputs)

# Define the model that will turn
# `encoder_input_data` & `decoder_input_data` into `decoder_target_data`
model = Model([encoder_inputs, decoder_inputs], decoder_outputs)

# Run training
model.compile(optimizer='rmsprop', loss='categorical_crossentropy')
model.fit([encoder_input_data[:num_samples].argmax(-1), decoder_input_data[:num_samples].argmax(-1)], decoder_target_data[:num_samples],
          batch_size=batch_size,
          epochs=epochs,
          validation_split=0.2)#train the model on the num_samples first samples
# Save model
model.save('s2s.h5')

# Next: inference mode (sampling).
# Here's the drill:
# 1) encode input and retrieve initial decoder state
# 2) run one step of decoder with this initial state
# and a "start of sequence" token as target.
# Output will be the next target token
# 3) Repeat with the current target token and current states

# Define sampling models
encoder_model = Model(encoder_inputs, encoder_states)

decoder_state_input_h = Input(shape=(latent_dim,))
decoder_state_input_c = Input(shape=(latent_dim,))
decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
decoder_outputs, state_h, state_c = decoder_lstm(
    embedded_decoder_input, initial_state=decoder_states_inputs)
decoder_states = [state_h, state_c]
decoder_outputs = decoder_dense(decoder_outputs)
decoder_model = Model(
    [decoder_inputs] + decoder_states_inputs,
    [decoder_outputs] + decoder_states)

# Reverse-lookup token index to decode sequences back to
# something readable.
reverse_input_char_index = dict(
    (i, char) for char, i in input_token_index.items())
reverse_target_char_index = dict(
    (i, char) for char, i in target_token_index.items())


def decode_sequence(input_seq):
    # Encode the input as state vectors.
    states_value = encoder_model.predict(input_seq.argmax(-1))

    # Generate empty target sequence of length 1.
    target_seq = np.zeros((1, 1, num_decoder_tokens))
    # Populate the first character of target sequence with the start character.
    target_seq[0, 0, target_token_index['\t']] = 1.

    # Sampling loop for a batch of sequences
    # (to simplify, here we assume a batch of size 1).
    stop_condition = False
    decoded_sentence = []
    while not stop_condition:
        output_tokens, h, c = decoder_model.predict(
            [target_seq.argmax(-1)] + states_value)

        # Sample a token
        sampled_token_index = np.argmax(output_tokens[0, -1, :])
        sampled_char = reverse_target_char_index[sampled_token_index]
        decoded_sentence.append(sampled_char)

        # Exit condition: either hit max length
        # or find stop character.
        if (len(decoded_sentence) > max_decoder_seq_length) or (sampled_char == '\n'):
            stop_condition = True

        # Update the target sequence (of length 1).
        target_seq = np.zeros((1, 1, num_decoder_tokens))
        target_seq[0, 0, sampled_token_index] = 1.

        # Update states
        states_value = [h, c]

    return decoded_sentence



import pdb
#pdb.set_trace()
index = 17400 #please hurry up
input_seq = encoder_input_data[index: index+1]
#index = np.random.randint(len(input_texts))
decoded_sentence = decode_sequence(input_seq)
print('-')
print('Input sentence:', input_texts[index])
print('Decoded sentence:', decoded_sentence)

index = 17401 #he has taken my wallet
input_seq = encoder_input_data[index: index+1]
#index = np.random.randint(len(input_texts))
decoded_sentence = decode_sequence(input_seq)
print('-')
print('Input sentence:', input_texts[index])
print('Decoded sentence:', decoded_sentence)

index = 17402 #sju sjösjuka...
input_seq = encoder_input_data[index: index+1]
#index = np.random.randint(len(input_texts))
decoded_sentence = decode_sequence(input_seq)
print('-')
print('Input sentence:', input_texts[index])
print('Decoded sentence:', decoded_sentence)

index = 17403 #du har inget...
input_seq = encoder_input_data[index: index+1]
#index = np.random.randint(len(input_texts))
decoded_sentence = decode_sequence(input_seq)
print('-')
print('Input sentence:', input_texts[index])
print('Decoded sentence:', decoded_sentence)


