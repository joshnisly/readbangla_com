#!/usr/bin/python

import pyaudio
import wave

CHUNK = 1024

def play_wav(wav_path):
    wav_file = wave.open(wav_path, 'rb')

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wav_file.getsampwidth()),
                    channels=wav_file.getnchannels(),
                    rate=wav_file.getframerate(),
                    output=True)

    data = wav_file.readframes(CHUNK)

    while data != '':
        stream.write(data)
        data = wav_file.readframes(CHUNK)

    stream.stop_stream()
    stream.close()

    p.terminate()
