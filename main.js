/* SPDX-License-Identifier: MIT */
/* SPDX-FileCopyrightText: Copyright 2025 Sam Blenny */
"use strict";

// Connection status span
const STATUS = document.querySelector('#status');

// Play button
const CONNECT = document.querySelector('#connect');

// Serial port reader
var READER = null;

// Audio context needs to be enabled in a handler for a user interaction event,
// so for now, just use null to indicate that audio isn't ready yet.
const AUDIO = {
    ctx: null,
    warningCounter: 0,
};

// Update status line span
function setStatus(s) {
    STATUS.textContent = s;
}

// Handle complete lines of serial port input
async function handleLine(line, state) {
    // =================================================
    // TODO: Implement a mechanic for playing Morse Code
    // =================================================
    console.log(line)
}

// Parse a chunk of serial data to assemble complete lines.
// CAUTION: This expects '\r\n' line endings!
async function parseChunk(chunk, state) {
    if (!state.lineSync) {
        // Ignore everything up to the first line ending, then start buffering
        // the next line
        const n = chunk.indexOf('\r\n');
        if (n >= 0) {
            state.lineBuf = (chunk.slice(n+2));
            state.lineSync = true;
        }
    } else {
        // Once line sync is locked, just append the next chunk
        state.lineBuf += chunk;
    }
    // Parse complete lines off the front of the buffered chunks
    var i = state.lineBuf.indexOf('\r\n');
    while(i >= 0) {
        const line = state.lineBuf.substr(0, i);
        state.lineBuf = state.lineBuf.substr(i+2);
        handleLine(line, state);
        i = state.lineBuf.indexOf('\r\n');
    }
}

// Buffer serial port data into lines (close port when done)
async function readLines(port) {
    const state = {
        lineSync: false,
        lineBuf: '',
        data: [],
        memFree: '',
    };
    const decoder = new TextDecoderStream();
    const pipeClosedPromise = port.readable.pipeTo(decoder.writable);
    READER = decoder.readable.getReader();
    try {
        while (true) {
            const {value, done} = await READER.read();
            if (done) {
                break;
            }
            if (value) {
                parseChunk(value, state);
            }
        }
    } catch (err) {
        // expected on cancel / disconnect
        console.log("readLines while(true) try/catch:", err);
    } finally {
        // Carefully release stream locks so .close() will work. Awaiting the
        // promise for the pipe to close is necessary to avoid an error.
        READER.releaseLock();
        await pipeClosedPromise.catch(() => {/* this makes it all be ok */});
        await port.close();
        CONNECT.classList.remove('on', 'mute');
        CONNECT.textContent = 'Connect';
        setStatus('[no connection]');
        console.log("serial disconnected");
    }
}

// Disconnect serial port and stop updating the canvas
async function serialDisconnect() {
    try {
        READER.cancel();
    } catch (err) {
        console.warn('disconnect error', err);
    }
}

// Attempt to start Web Serial connection
function serialConnect() {
    if (!('serial' in navigator)) {
        setStatus('Browser does not support Web Serial');
        alert('This browser does not support Web Serial');
    }
    // Define a filter for Adafruit's USB vendor ID
    const adafruitVIDFilter = [{usbVendorId: 0x239a}];
    // Request access to serial port (trigger a browser permission prompt)
    navigator.serial
    .requestPort({filters: adafruitVIDFilter})
    .then(async (response) => {
        const port = await response;
        port.ondisconnect = async (event) => {
            console.log('serial device unplugged');
            serialDisconnect();
        };
        await port.open({baudRate: 115200});
        // Update HTML button & status indicator
        CONNECT.classList.add('on');
        CONNECT.textContent = 'disconnect';
        setStatus('connected');
        console.log('serial connected');
        initAudioSystem();
        // Begin reading buffered lines
        readLines(port);
    })
    .catch((err) => {
        setStatus('no serial port selected');
    });
}

// Set up audio (this must be called from a user interaction event handler)
function initAudioSystem() {
    const context = window.AudioContext || window.webkitAudioContext;
    if(!context) {
        console.log("AudioContext not available (Lockdown Mode enabled?)");
        alert("The WebAudio API is disabled, so I can't play sounds. For iOS "
            + "with Lockdown Mode enabled, you could try disabling Lockdown "
            + "Mode for this page (\"AA\" menu in URL bar).");
    } else {
        AUDIO.ctx = new context();
        AUDIO.ctx.resume().then(() => {
            CONNECT.classList.add('mute');
            console.log("audio resumed");
        });
    }
}

// Add serial connect and audio playback enable function to connect button
CONNECT.addEventListener('click', function() {
    if(CONNECT.classList.contains('on')) {
        serialDisconnect();
        // Mute audio and release the old audio context. This makes sure that
        // audio currently playing will stop rather than resuming when audio
        // gets unmuted again later.
        try {
            AUDIO.ctx.suspend().then(() => {
                CONNECT.classList.remove('mute');
                AUDIO.ctx = null;
            });
        } catch (err) {
            console.warn('audio suspend() error:', err);
        }
    } else {
        serialConnect();
    }
});

function playSound() {
    if(!AUDIO.ctx) {
        // Audio is muted, so we can't play sounds right now
        if(AUDIO.warningCounter < 1) {
            console.log("To play sound, you need to click the unmute button");
            AUDIO.warningCounter += 1;
        }
        return
    }
    // Audio is unmuted, so play sound

    // ===========================
    // TODO: AUDIO.ctx.<something>
    // ===========================
}
