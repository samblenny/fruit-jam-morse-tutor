#!/bin/sh
# Slice wav around silence of -63dB or less lasting 90 ms or longer
sox itu-morse-normalized.wav -r 8000 -c 1 out_.wav \
 silence 1 0.09 -63dB 1 0.09 -63dB : newfile : restart pad 0.008 0.008
