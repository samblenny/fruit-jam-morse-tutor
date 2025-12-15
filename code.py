# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2025 Sam Blenny
#
# See NOTES.md for documentation links
#
import time


# TODO: Do something useful

n = 0
while True:
    # spin forever to prevent annoying end-of-code yellow blinking NeoPixels
    time.sleep(2)
    print(n)
    n += 1
