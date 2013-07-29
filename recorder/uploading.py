#!/usr/bin/python

import httplib
import threading
import time
import os
import Queue

HOST = 'www.readbangla.com'
PORT = 80
PATH = '/upload_recording/'

class _UploadThread(threading.Thread):
    def __init__(self, message_queue, parent):
        threading.Thread.__init__(self)
        self._message_queue = message_queue
        self._parent = parent

    def run(self):
        try:
            while True:
                file_path = self._message_queue.get()
                print file_path
                if file_path is None:
                    break

                self._upload_file(file_path)
                time.sleep(0.1)
        except Exception, e:
            text = str(e)
            self._parent.on_error(text)


    def _upload_file(self, file_path):
        try:
            conn = httplib.HTTPConnection(HOST, PORT)
            body = open(file_path, 'rb')
            conn.request('POST', PATH, body=body)
            res = conn.getresponse()
            print res.status
            print res.read()
        except Exception, e:
            print e
            self._message_queue.put(file_path)
            return

        os.unlink(file_path)
        

class Uploader(object):
    def __init__(self, parent):
        self._message_queue = Queue.Queue()
        self._upload_thread = _UploadThread(self._message_queue, parent)
        self._upload_thread.start()

    def add_item(self, file_path):
        self._message_queue.put(file_path)

    def quit(self):
        self._message_queue.put(None)

