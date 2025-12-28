# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2025 Sam Blenny
#
# See NOTES.md for documentation links
#
from audiobusio import I2SOut
import audiocore
from board import (
    I2C, I2S_BCLK, I2S_DIN, I2S_MCLK, I2S_WS, PERIPH_RESET
)
from digitalio import DigitalInOut, Direction, Pull
import displayio
import gc
from micropython import const
from pwmio import PWMOut
import synthio
import time
import ulab.numpy as np

from adafruit_tlv320 import TLV320DAC3100


from lessons import LESSONS
from sb_morse import MorseKeyer


# Morse Code Options
SIDETONE_HZ = const(650)

# DAC and Synthesis parameters
SAMPLE_RATE = const(8000)
CHAN_COUNT  = const(1)
BUFFER_SIZE = const(256)

# I2S MCLK clock frequency
MCLK_HZ = const(15_000_000)



def configure_dac(i2c, sample_rate, mclk_hz):
    # Configure TLV320DAC (this requires a separate 15 MHz PWMOut to MCLK)

    # 1. Initialize DAC (this includes a soft reset and sets minimum volumes)
    dac = TLV320DAC3100(i2c)

    # 2. Configure headphone/speaker routing and volumes (order matters here)
    dac.speaker_output = False
    dac.headphone_output = True
    dac.dac_volume = -3  # Keep this below 0 to avoid DSP filter clipping
    dac.headphone_volume = 0  # CAUTION! Line level. Too loud for headphones!

    # 3. Configure the right PLL and CODEC settings for our sample rate
    dac.configure_clocks(sample_rate=sample_rate, mclk_freq=MCLK_HZ)

    # 4. Wait for power-on volume ramp-up to finish
    time.sleep(0.35)
    return dac


def run():

    displayio.release_displays()
    gc.collect()

    # Set up I2C and I2S buses
    i2c = I2C()
    audio = I2SOut(bit_clock=I2S_BCLK, word_select=I2S_WS, data=I2S_DIN)

    # Set up 15 MHz MCLK PWM clock output for less hiss and distortion
    mclk_pwm = PWMOut(I2S_MCLK, frequency=MCLK_HZ, duty_cycle=2**15)

    # Initialize DAC for 8 kHz sample rate
    dac = configure_dac(i2c, SAMPLE_RATE, MCLK_HZ)

    # Load 12 WPM wav files (100ms dit, 300ms dah)
    dit = audiocore.WaveFile("dit_8kHz_12wpm.wav")
    dah = audiocore.WaveFile("dah_8kHz_12wpm.wav")

    # Morse Code timing generator
    gc.collect()
    mk = MorseKeyer()
    gc.collect()

    # Cache function and number references (go faster)
    sleep = time.sleep
    play = audio.play
    ditsec = mk.sec_per_dot
    dahsec = ditsec * 3

    # Send some Morse code on the Fruit Jam DAC
    while True:
        msg = "CQ PARIS 123. <AR>"
        print(f"playing: {msg}")
        for (on_sec, off_sec) in mk.timings(msg):
            if on_sec == ditsec:
                play(dit)
            else:
                play(dah)
            sleep(on_sec + off_sec)
        sleep(2)

run()
