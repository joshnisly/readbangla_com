#!/usr/bin/python

import httplib
import threading
import time
import os
import Queue

import helpers

PATH = '/recordings/upload/'

class _UploadThread(threading.Thread):
    def __init__(self, message_queue, parent, username, password):
        threading.Thread.__init__(self)
        self._message_queue = message_queue
        self._parent = parent
        self._username = username
        self._password = password

    def run(self):
        try:
            while True:
                message = self._message_queue.get()
                if message is None:
                    break

                file_path, word_str = message
                self._upload_file(file_path, word_str)
                time.sleep(1)
        except Exception, e:
            text = unicode(e.message)
            self._parent.on_error(text)


    def _upload_file(self, file_path, word_str):
        try:
            body = open(file_path, 'rb')
            query_parms = {
                'word': word_str.encode('utf8')
            }
            response = helpers.request_with_auth(PATH, self._username, self._password,
                                                 query_parms=query_parms, post_data=body)
        except Exception, e:
            print 'error'
            print e
            #open('error.txt', 'wb').write(
            self._parent.on_error(unicode(e.message))
            self._message_queue.put(file_path)
            return

        os.unlink(file_path)
        

class Uploader(object):
    def __init__(self, parent, username, password):
        self._message_queue = Queue.Queue()
        self._upload_thread = _UploadThread(self._message_queue, parent, username, password)
        self._upload_thread.start()

    def add_item(self, file_path, word_str):
        self._message_queue.put((file_path, word_str))

    def quit(self):
        self._message_queue.put(None)

