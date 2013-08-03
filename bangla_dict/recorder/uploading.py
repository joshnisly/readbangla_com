#!/usr/bin/python

import httplib
import threading
import time
import os
import Queue

import helpers

PATH = '/recordings/upload/'

class _UploadThread(threading.Thread):
    def __init__(self, message_queue, parent, host, port, username, password):
        threading.Thread.__init__(self)
        self._message_queue = message_queue
        self._parent = parent
        self._host = host
        self._port = port
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
            print e
            text = unicode(e.message)
            self._parent.on_error(text)


    def _upload_file(self, file_path, word_str):
        try:
            body = open(file_path, 'rb')
            query_parms = {
                'word': word_str.encode('utf8')
            }
            self._parent.on_status_update(u'Uploading %s...' % word_str)
            response = helpers.request_with_auth(self._host, self._port, PATH,
                                                 self._username, self._password,
                                                 query_parms=query_parms, post_data=body)
            body.close()
            self._parent.on_status_update('Ready.')
        except helpers.ServerError, e:
            self._parent.on_status_update('Server error.')
            print e
            self._parent.on_error(unicode(e.message))
            return
        except Exception, e:
            self._parent.on_status_update('Error.')
            print e
            self._parent.on_error(unicode(e.message))
            self._message_queue.put((file_path, word_str))
            return

        os.unlink(file_path)
        

class Uploader(object):
    def __init__(self, parent, host, port, username, password):
        self._message_queue = Queue.LifoQueue()
        self._upload_thread = _UploadThread(self._message_queue, parent, host, port, username, password)
        self._upload_thread.start()

    def add_item(self, file_path, word_str):
        self._message_queue.put((file_path, word_str))

    def quit(self):
        self._message_queue.put(None)

