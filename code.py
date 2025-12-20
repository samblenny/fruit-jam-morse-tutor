# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2025 Sam Blenny
#
# See NOTES.md for documentation links
#
from audiobusio import I2SOut
from board import (
    I2C, I2S_BCLK, I2S_DIN, I2S_MCLK, I2S_WS, PERIPH_RESET
)
from digitalio import DigitalInOut, Direction, Pull
import displayio
import gc
from micropython import const
import synthio
import time
import ulab.numpy as np

from adafruit_tlv320 import TLV320DAC3100


from lessons import LESSONS
from sb_morse import MorseKeyer


# Morse Code Options
SIDETONE_HZ = const(650)

# DAC and Synthesis parameters
SAMPLE_RATE = const(44100)
CHAN_COUNT  = const(1)
BUFFER_SIZE = const(1024)
#==============================================================
# CAUTION! When this is set to True, the headphone jack will
# send a line-level output suitable use with a mixer or powered
# speakers, but that will be _way_ too loud for earbuds. For
# finer control of line level volume, adjust LL_DAC_VOLUME.
LINE_LEVEL = const(True)
LL_HEADPHONE_VOLUME = 0
#==============================================================


def init_dac_audio_synth(i2c):
    # Configure Fruit Jam rev D TLV320 I2S DAC and make a Synthesizer.
    gc.collect()
    # 1. Reset DAC (reset is active low)
    rst = DigitalInOut(PERIPH_RESET)
    rst.direction = Direction.OUTPUT
    rst.value = False
    time.sleep(0.1)
    rst.value = True
    time.sleep(0.05)
    # 2. Configure sample rate, bit depth, and output port
    dac = TLV320DAC3100(i2c)
    dac.configure_clocks(sample_rate=SAMPLE_RATE, bit_depth=16)
    dac.speaker_output = False
    dac.headphone_output = True
    # 3. Adjust volume for for line-level if needed, otherwise use default
    #    volume set by `dac.headphone_output = True`
    if LINE_LEVEL:
        # This gives a line output level suitable for plugging into a mixer or
        # the AUX input of a powered speaker (THIS IS TOO LOUD FOR HEADPHONES!)
        dac.headphone_volume = LL_HEADPHONE_VOLUME
    # 4. Configure I2S for Fruit Jam rev D
    audio = I2SOut(bit_clock=I2S_BCLK, word_select=I2S_WS, data=I2S_DIN)
    # 5. Configure synthio patch to generate sine wave notes
    vca = synthio.Envelope(
        attack_time=0.01, decay_time=0, sustain_level=0.95,
        release_time=0.03, attack_level=0.95
    )
    sine_samples = round(SAMPLE_RATE * 10 / SIDETONE_HZ)
    sinewave = np.array(
        np.sin(np.linspace(0, 2*np.pi, sine_samples, endpoint=False)) * 32760,
        dtype=np.int16
    )
    synth = synthio.Synthesizer(
        sample_rate=SAMPLE_RATE, channel_count=CHAN_COUNT, #envelope=vca,
        waveform=sinewave
    )
    audio.play(synth)
    return (dac, audio, synth)


def run():

    displayio.release_displays()
    gc.collect()

    # Set up the audio stuff for a basic synthesizer
    i2c = I2C()
    (dac, audio, synth) = init_dac_audio_synth(i2c)

    # Morse Code timing generator
    gc.collect()
    mk = MorseKeyer()
    gc.collect()

    # Debug dump Morse timing info
    print()
    print("Morse Characters and Prosigns:", mk.chars)
    print()

    # Cache function references (go faster)
    Note = synthio.Note
    sleep = time.sleep
    press = synth.press
    release = synth.release

    # Send some Morse code on the Fruit Jam DAC
    note = Note(frequency=SIDETONE_HZ)
    while True:
        msg = "PARIS. <AR>"
        for (on_sec, off_sec) in mk.timings(msg):
            press(note)
            sleep(on_sec)
            release(note)
            sleep(off_sec)

run()
