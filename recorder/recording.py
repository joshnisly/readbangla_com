#!/usr/bin/python

import array
import threading
import os
import pyaudio
import Queue
import struct
import sys
import time
import wave

THRESHOLD = 1500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100
MAXIMUM = 16384

class _RecordThread(threading.Thread):
    def __init__(self, output_path, message_queue, parent):
        threading.Thread.__init__(self)
        self._output_path = output_path
        self._message_queue = message_queue
        self._parent = parent

        self._pyaudio = pyaudio.PyAudio()
        self._is_recording = False
        self._stream = None
        self._audio = array.array('h')
        self._num_audible = 0
        self._num_silent = 0
        self._should_normalize = True
        self._threshold = THRESHOLD

    def __del__(self):
        self._pyaudio.terminate()

    def run(self):
        while True:
            event = None
            timeout = 0 if self._is_recording else 0.1
            try:
                event = self._message_queue.get(timeout=timeout)
            except Queue.Empty:
                pass
            else:
                if event is None:
                    if self._is_recording:
                        self._finish()
                    break

            if event == 'start':
                self._should_normalize = True
                self._start()

            if event == 'startnonormalize':
                self._should_normalize = False
                self._start()

            if event == 'stop':
                self._finish()

            if self._stream:
                snd_data = array.array('h', self._stream.read(CHUNK_SIZE))
                if sys.byteorder == 'big':
                    snd_data.byteswap()

                # See if we need to stop
                silent = self._is_silent(snd_data)
                if silent:
                    if self._num_audible > 15:
                        self._num_silent += 1
                else:
                    self._num_audible += 1
                    self._num_silent = 0

                if self._num_silent > 15 and self._should_normalize:
                    self._finish()
                    continue

                self._audio.extend(snd_data)

    def is_recording(self):
        return self._is_recording

    def get_90th_percentile(self):
        data = [abs(x) for x in list(self._audio)]
        data.sort()
        data = data[int(len(data) * 0.95):]
        return data[0]

    def set_threshold(self, threshold):
        self._threshold = threshold

    def _start(self):
        assert not self._is_recording
        self._is_recording = True
        self._audio = array.array('h')
        self._stream = self._pyaudio.open(format=FORMAT, channels=1, rate=RATE,
                                          input=True, output=True,
                                          frames_per_buffer=CHUNK_SIZE)

    def _finish(self):
        assert self._is_recording

        sample_width = self._pyaudio.get_sample_size(FORMAT)
        self._stream.stop_stream()
        self._stream.close()
        self._stream = None

        data = self._audio
        if self._should_normalize:
            data = self._trim_silence(data)
            data = self._normalize(data)
        data = struct.pack('<' + ('h'*len(data)), *data)

        if os.path.exists(self._output_path):
            os.unlink(self._output_path)
        wf = wave.open(self._output_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(sample_width)
        wf.setframerate(RATE)
        wf.writeframes(data)
        wf.close()

        self._is_recording = False
        self._num_audible = 0
        self._num_silent = 0
        self._parent.on_recording_finish()

    def _normalize(self, snd_data):
        adjustment_factor = float(MAXIMUM)/max(abs(i) for i in snd_data)

        normalized_data = array.array('h')
        for i in snd_data:
            normalized_data.append(int(i*adjustment_factor))
        return normalized_data

    def _trim_silence(self, snd_data):
        def _trim(snd_data):
            snd_started = False
            r = array.array('h')

            for i in snd_data:
                if not snd_started and abs(i) > self._threshold:
                    snd_started = True
                    r.append(i)

                elif snd_started:
                    r.append(i)
            return r

        # Trim to the left
        snd_data = _trim(snd_data)

        # Trim to the right
        snd_data.reverse()
        snd_data = _trim(snd_data)
        snd_data.reverse()
        return snd_data

    def _is_silent(self, snd_data):
        print max(snd_data) < self._threshold, self._threshold
        return max(snd_data) < self._threshold

class Recorder(object):
    def __init__(self, output_path, parent):
        self._message_queue = Queue.Queue()
        self._record_thread = _RecordThread(output_path, self._message_queue, parent)
        self._record_thread.start()

    def start_stop(self, should_normalize=True):
        if self.is_recording():
            self._message_queue.put('stop')
        else:
            self._message_queue.put('start' if should_normalize else 'startnonormalize')

        time.sleep(0.1)

    def set_threshold(self, threshold):
        self._record_thread.set_threshold(threshold)

    def get_90th_percentile(self):
        return self._record_thread.get_90th_percentile()

    def is_recording(self):
        return self._record_thread.is_recording()

    def quit(self):
        self._message_queue.put(None)


