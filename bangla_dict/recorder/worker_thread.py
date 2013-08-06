#!/usr/bin/python

import threading
import Queue

class WorkerThread(threading.Thread):
    def __init__(self, message_queue, parent):
        threading.Thread.__init__(self)
        self._message_queue = message_queue
        self._parent = parent

    def _get_timeout(self):
        return None

    # Event will be None if waiting for an event timed out.
    def _process_event(self, event):
        assert False

    def _cleanup(self):
        pass

    def run(self):
        while True:
            event = None
            try:
                event = self._message_queue.get(timeout=self._get_timeout())
            except Queue.Empty:
                event = None
            else:
                if event is None:
                    self._cleanup()
                    return

            try:
                self._process_event(event)
            except Exception, e:
                self._parent.on_error(unicode(e.message))

