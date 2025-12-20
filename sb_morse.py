# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2025 Sam Blenny
#
# See NOTES.md for documentation links
#
import re


def encode_chars(s):
    # Convert Morse Code character heredoc string to a dictionary of Morse
    # character key strings and timing pattern tuple values
    chars = {}
    char_re = re.compile(r'^(\S+)\s(\S+).*')
    for line in s.split('\n'):
        m = char_re.match(line)
        if m is None:
            continue
        (key, morse) = m.groups()
        dd_list = []
        for ditdah in morse:
            if ditdah == '.':
                dd_list.append(1)
            elif ditdah == '-':
                dd_list.append(3)
            else:
                raise ValueError(
                    f'Unexpected dit-dah pattern: \'{ditdah}\' in "{line}"')
        chars[key] = tuple(dd_list)
    return chars


class MorseKeyer:

    def __init__(self, wpm=12):
        # WPM Calculation, PARIS method @ 50 dots per word:
        # - dot time = (60 s) / (50 dots) / wpm = 1.20/wpm s/dot
        # -  5 WPM: 1.2/5  = 0.24 s/dot
        # -  8 WPM: 1.2/8  = 0.15 s/dot
        # - 12 WPM: 1.2/12 = 0.10 s/dot
        self.wpm = wpm
        self.sec_per_dot = 60 / 50 / wpm

        # Create dictionary mapping ASCII characters or prosigns strings to
        # tuples of signal on-times for the corresponding dit-dah patterns
        self.chars = encode_chars("""
A .-
B -...
C -.-.
D -..
E .
F ..-.
G --.
H ....
I ..
J .---
K -.-
L .-..
M --
N -.
O ---
P .--.
Q --.-
R .-.
S ...
T -
U ..-
V ...-
W .--
X -..-
Y -.--
Z --..
1 .----
2 ..---
3 ...--
4 ....-
5 .....
6 -....
7 --...
8 ---..
9 ----.
0 -----
. .-.-.-
, --..--
: ---...
? ..--..
' .----.
- -....-
/ -..-.
( -.--.
) -.--.-
" .-..-.
= -...- # ITU = is same as ham <BT> prosign (pause)
+ .-.-. # ITU + is same as ham <AR> prosign (end of TX / message separator)
<BT> -...-
<AR> .-.-.
@ .--.-.
<SK> ...-.- # ITU: End of work, Ham: end of final TX of a QSO
<BK> -...-.- # Ham: Break in Transmission (expecting other station to reply)
""")

    def timings(self, text):
        # Generator yielding (on, off) timing tuples for text encoded as Morse
        text = text.strip()  # remove extraneous whitespace
        if not text:
            return None

        spd = self.sec_per_dot

        # Parse text
        start = end = 0
        while start < len(text):

            # Find start and end indexes of next token (ASCII char or prosign)
            if text[start] == '<':
                # Prosigns start with '<' (e.g. <AR>, <BT>, etc)
                end = text.find('>', start) + 1
                if end == 0 or end > len(text):
                    raise ValueError(
                        f"Prosign syntax error, missing '>': '{text[start:]}'")
            else:
                # Regular character
                end = start + 1

            # Consume this character or prosign
            key = text[start:end].upper()
            if not key in self.chars:
                raise ValueError(f"Not a Morse character or prosign: {key}")
            on_times = self.chars[key]
            start = end

            # Detect and consume trailing whitespace, if any is present
            need_word_space = False
            while start < len(text) and text[start] in (' ', '\r', '\n'):
                need_word_space = True
                start = end = start + 1

            # Yield on-off timing pairs for the character (or prosign). The
            # off times depend on whether the dit or dah was at the end of a
            # word, at the end of a character inside a word, or inside a
            # character.
            #
            # ITU-R 1677 Morse Code Timing:  3 dots per dash, 1 dot symbol gap,
            # 3 dot character gap, 7 dot word gap
            for (i, on_time) in enumerate(on_times):
                if i + 1 == len(on_times):
                    if need_word_space:
                        yield (on_time * spd, 7 * spd)  # end of word
                    else:
                        yield (on_time * spd, 3 * spd)  # end of character
                else:
                    yield (on_time * spd, 1 * spd)      # inside character
