#!/usr/bin/python

import pyaudio
import Queue
import wave

import worker_thread

CHUNK = 1024

class PlayerThread(worker_thread.WorkerThread):
    def __init__(self, message_queue, parent, wav_path):
        worker_thread.WorkerThread.__init__(self, message_queue, parent)

        self._is_playing = False
        self._wav_path = wav_path

        self._pyaudio = pyaudio.PyAudio()
        self._wav_file = None
        self._stream = None

    def is_playing(self):
        return self._is_playing

    def __del__(self):
        self._pyaudio.terminate()

    def _get_timeout(self):
        return 0 if self._is_playing else 0.1

    def _process_event(self, event):
        if event == 'start':
            assert not self._is_playing
            self._wav_file = wave.open(self._wav_path, 'rb')

            wav_format = self._pyaudio.get_format_from_width(self._wav_file.getsampwidth())
            self._stream = self._pyaudio.open(format=wav_format,
                                              channels=self._wav_file.getnchannels(),
                                              rate=self._wav_file.getframerate(),
                                              output=True)
            self._is_playing = True

        if event == 'stop' and self._is_playing:
            self._stop()

        if self._is_playing:
            data = self._wav_file.readframes(CHUNK)

            if not data:
                self._stop()

            self._stream.write(data)

    def _stop(self):
        if not self._stream:
            return

        self._stream.stop_stream()
        self._stream.close()
        self._wav_file.close()
        self._is_playing = False

class Player(object):
    def __init__(self, wav_path, parent):
        self._message_queue = Queue.Queue()
        self._thread = PlayerThread(self._message_queue, parent, wav_path)
        self._thread.start()

    def is_playing(self):
        return self._thread.is_playing()

    def start(self):
        self._message_queue.put('start')

    def stop(self):
        self._message_queue.put('stop')

    def quit(self):
        self._message_queue.put(None)

