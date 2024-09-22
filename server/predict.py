# 
# Copyright 2016 Google Inc.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 


import magenta

from magenta.models.melody_rnn import melody_rnn_config_flags
from magenta.models.melody_rnn import melody_rnn_model
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from magenta.protobuf import generator_pb2
from magenta.protobuf import music_pb2


import os
import time
import tempfile
import pretty_midi
import magenta
from magenta.models.melody_rnn import melody_rnn_model, melody_rnn_sequence_generator
from magenta.protobuf import generator_pb2
from magenta.protobuf import music_pb2
import os
import tempfile
import pretty_midi

# Use a pre-trained model with real-world data
def initialize_real_world_model():
    BUNDLE_NAME = 'attention_rnn'
    STEPS_PER_QUARTER = 4
    bundle_file = magenta.music.read_bundle_file(os.path.abspath(BUNDLE_NAME + '.mag'))
    
    # Load pre-trained config
    config = melody_rnn_model.default_configs[BUNDLE_NAME]
    generator = melody_rnn_sequence_generator.MelodyRnnSequenceGenerator(
        model=melody_rnn_model.MelodyRnnModel(config),
        details=config.details,
        steps_per_quarter=STEPS_PER_QUARTER,
        bundle=bundle_file
    )
    return generator

# Generate music based on the pre-trained model
def generate_real_music(generator, total_seconds=60):
    # Create an empty primer sequence or use a real-world MIDI file as the primer
    primer_sequence = music_pb2.NoteSequence()
    
    # Generator options (you can customize start and end times here)
    generator_options = generator_pb2.GeneratorOptions()
    generator_options.generate_sections.add(start_time=0, end_time=total_seconds)
    
    # Generate a music sequence
    generated_sequence = generator.generate(primer_sequence, generator_options)
    
    # Save and return the generated music
    output = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
    magenta.music.midi_io.sequence_proto_to_midi_file(generated_sequence, output.name)
    return output.name

# Play the generated music (or output it to a synthesizer)
def play_real_music(midi_file):
    midi_data = pretty_midi.PrettyMIDI(midi_file)
    
    # Play the generated MIDI data using a MIDI player
    # Alternatively, you can convert it to audio and play using an audio library
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            print(f"Playing note: {note.pitch} with velocity {note.velocity}")


BUNDLE_NAME = 'attention_rnn'

config = magenta.models.melody_rnn.melody_rnn_model.default_configs[BUNDLE_NAME]
bundle_file = magenta.music.read_bundle_file(os.path.abspath(BUNDLE_NAME+'.mag'))
steps_per_quarter = 4

generator = melody_rnn_sequence_generator.MelodyRnnSequenceGenerator(
      model=melody_rnn_model.MelodyRnnModel(config),
      details=config.details,
      steps_per_quarter=steps_per_quarter,
      bundle=bundle_file)

def _steps_to_seconds(steps, qpm):
    return steps * 60.0 / qpm / steps_per_quarter

def generate_midi(midi_data, total_seconds=10):
    primer_sequence = magenta.music.midi_io.midi_to_sequence_proto(midi_data)

    # predict the tempo
    if len(primer_sequence.notes) > 4:
        estimated_tempo = midi_data.estimate_tempo()
        if estimated_tempo > 240:
            qpm = estimated_tempo / 2
        else:
            qpm = estimated_tempo
    else:
        qpm = 120
    primer_sequence.tempos[0].qpm = qpm

    generator_options = generator_pb2.GeneratorOptions()
    # Set the start time to begin on the next step after the last note ends.
    last_end_time = (max(n.end_time for n in primer_sequence.notes)
                     if primer_sequence.notes else 0)
    generator_options.generate_sections.add(
        start_time=last_end_time + _steps_to_seconds(1, qpm),
        end_time=total_seconds)

    # generate the output sequence
    generated_sequence = generator.generate(primer_sequence, generator_options)

    output = tempfile.NamedTemporaryFile()
    magenta.music.midi_io.sequence_proto_to_midi_file(generated_sequence, output.name)
    output.seek(0)
    return output
