#!/usr/bin/python

import httplib
import threading
import time
import os
import Queue

import helpers
import worker_thread

PATH = '/recordings/upload/'

class _UploadThread(worker_thread.WorkerThread):
    def __init__(self, message_queue, parent, host, port, username, password):
        worker_thread.WorkerThread.__init__(self, message_queue, parent)
        self._host = host
        self._port = port
        self._username = username
        self._password = password

    def _process_event(self, event):
        file_path, word_str = event
        self._upload_file(file_path, word_str)

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

