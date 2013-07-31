#!/usr/bin/python

import ConfigParser
import os
import pyaudio
import play
from PyQt4 import QtCore, QtGui
import Queue
import sys
import threading
import time

import helpers
import recording
import uploading

class Settings(object):
    def __init__(self, path):
        self._values = {}
        self._path = path
        parser = ConfigParser.ConfigParser()
        parser.read(path)
        if parser.has_section('Settings'):
            for setting, value in parser.items('Settings'):
                self._values[setting.lower()] = value

    def save(self):
        parser = ConfigParser.ConfigParser()
        for setting, value in self._values.items():
            parser.set('Settings', setting.lower(), value)
        parser.write(open(self._path, 'w'))


    def get_setting(self, setting, default=None):
        return self._values.get(setting.lower(), default)

    def set_setting(self, setting, value):
        self._values[setting.lower()] = values

class RecorderDialog(QtGui.QDialog):
    def __init__(self, working_dir, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle(self.tr('Bangla Recorder Client'))

        self._is_playing = False
        self._working_dir = working_dir

        self._remaining_words = []

        self._settings = Settings(os.path.join(self._working_dir, 'settings.ini'))

        self._temp_path = os.path.join(self._working_dir, 'temp', 'testing.wav')
        _ensure_parent_dir(self._temp_path)
        self._message_queue = Queue.Queue()
        self._recorder = recording.Recorder(self._temp_path, self)
        self._uploader = uploading.Uploader(self, self._settings.get_setting('username', ''),
                                            self._settings.get_setting('password', ''))

        self._error_to_display = None
        self._error_timer = QtCore.QTimer(self)
        self.connect(self._error_timer, QtCore.SIGNAL('timeout()'), self._display_error)
        self._error_timer.start(100)

        full_layout = QtGui.QVBoxLayout()

        top_buttons_layout = QtGui.QHBoxLayout()
        self._download_button = QtGui.QPushButton('&Download New Words')
        self.connect(self._download_button, QtCore.SIGNAL('clicked()'), self._download)
        top_buttons_layout.addWidget(self._download_button)
        top_buttons_layout.addStretch()
        self._calibrate_button = QtGui.QPushButton('&Calibrate')
        self.connect(self._calibrate_button, QtCore.SIGNAL('clicked()'), self._calibrate)
        top_buttons_layout.addWidget(self._calibrate_button)
        self._quit_button = QtGui.QPushButton('&Quit')
        self.connect(self._quit_button, QtCore.SIGNAL('clicked()'), self.reject)
        top_buttons_layout.addWidget(self._quit_button)
        full_layout.addLayout(top_buttons_layout)

        middle_layout = QtGui.QHBoxLayout()
        self._words_list = QtGui.QListWidget(self)
        font = self._words_list.font()
        font.setPointSize(16)
        self._words_list.setFont(font)
        self._words_list.setMaximumWidth(200)
        middle_layout.addWidget(self._words_list)
        middle_layout.addStretch()
        full_layout.addLayout(middle_layout)

        self.connect(self._words_list.selectionModel(), QtCore.SIGNAL('currentChanged(const QModelIndex&, const QModelIndex&)'), self._on_word_selected)

        recording_layout = QtGui.QVBoxLayout()
        recording_layout.setSpacing(20)
        recording_layout.setAlignment(QtCore.Qt.AlignHCenter)
        self._cur_word_label = QtGui.QLabel()
        font = self._cur_word_label.font()
        font.setPointSize(32)
        self._cur_word_label.setFont(font)
        self._cur_word_label.setAlignment(QtCore.Qt.AlignHCenter)
        recording_layout.addWidget(self._cur_word_label)
        self._record_button = QtGui.QPushButton('&Record')
        self.connect(self._record_button, QtCore.SIGNAL('clicked()'), self._start_stop_recording)
        recording_layout.addWidget(self._record_button)
        self._play_button = QtGui.QPushButton('&Play')
        self.connect(self._play_button, QtCore.SIGNAL('clicked()'), self._play_back)
        recording_layout.addWidget(self._play_button)
        self._upload_button = QtGui.QPushButton('&Upload file')
        self.connect(self._upload_button, QtCore.SIGNAL('clicked()'), self._convert_and_upload)
        recording_layout.addWidget(self._upload_button)

        for button in [self._record_button, self._play_button, self._upload_button]:
            font = button.font()
            font.setPointSize(15)
            button.setFont(font)
            button.setStyleSheet('padding: 20;')
            button.setMinimumWidth(250)

        recording_layout.addStretch()
        middle_layout.addLayout(recording_layout)
        middle_layout.addStretch()

        self.setLayout(full_layout)
        self.setMinimumSize(500, 350)

        self._download() # TODO: remove this after testing

    def reject(self):
        self._recorder.quit()
        self._uploader.quit()
        QtGui.QDialog.reject(self)

    def on_error(self, error):
        self._error_to_display = error

    def _display_error(self):
        if self._error_to_display:
            QtGui.QMessageBox.critical(self, 'Error', self._error_to_display)
            self._error_to_display = None
        
    def on_recording_finish(self):
        self._update_ui()

    def _download(self):
        try:
            response = helpers.request_with_auth('/recordings/needed_words/',
                                                 self._settings.get_setting('username', ''),
                                                 self._settings.get_setting('password', ''))
            self._remaining_words = response.split('\n')
        except Exception, e:
            self.on_error(str(e))

        self._update_ui(True)

    def _get_cur_word(self):
        cur_word = ''
        if self._words_list.count():
            cur_word = self._remaining_words[self._words_list.currentRow()]
        return cur_word

    def _update_ui(self, reload_words_list=False):
        if reload_words_list:
            while self._words_list.count() > 0:
                self._words_list.takeItem(0)

            self._words_list.addItems(self._remaining_words)
            self._words_list.setCurrentIndex(self._words_list.model().index(0, 0))

        self._cur_word_label.setText(self._get_cur_word())

        text = '&Stop Recording' if self._recorder.is_recording() else '&Record'
        self._record_button.setText(text)
        self._record_button.setCheckable(True)
        self._record_button.setChecked(self._recorder.is_recording())

        if self._is_playing:
            self._play_button.setText('&Playing...')
        else:
            self._play_button.setText('&Play')

    def _start_stop_recording(self):
        self._recorder.start_stop()
        self._update_ui()

    def _play_back(self):
        self._is_playing = True
        self._update_ui()
        play.play_wav(self._temp_path)
        self._is_playing = False
        self._update_ui()

    def _convert_and_upload(self):
        try:
            cur_word = self._get_cur_word()

            # Convert to MP3
            lame_path = self._get_lame_path()
            os.system(u'%s -mm -h %s %s' % (lame_path, self._temp_path, self._temp_path + '.mp3'))

            target_path = os.path.join(self._working_dir, 'outbox', cur_word + '.mp3')
            _ensure_parent_dir(target_path)
            os.rename(self._temp_path + '.mp3', target_path)

            self._uploader.add_item(target_path, cur_word)
        except Exception, e:
            self.on_error(str(e))

    def _on_word_selected(self, index, old_index):
        self._update_ui()

    def _calibrate(self):
        assert not self._recorder.is_recording()

        msg = 'This is the calibration feature. First, we will calibrate the silent volume levels.\n' +\
              'After clicking OK, remain silent and allow the software to measure silence.'
        response = QtGui.QMessageBox.information(self, 'Calibration, part 1', msg, QtGui.QMessageBox.Cancel|QtGui.QMessageBox.Ok)
        if response != QtGui.QMessageBox.Ok:
            return

        time.sleep(0.25)
        self._recorder.start_stop(False)
        time.sleep(2)
        self._recorder.start_stop()

        silence_level = self._recorder.get_90th_percentile() * 1.5
        msg = 'Silence calibration complete\nSound level: %i.' % silence_level
        response = QtGui.QMessageBox.information(self, 'Calibration, part 1', msg)
        self._recorder.set_threshold(silence_level)
        
    def _get_lame_path(self):
        if os.name == 'nt':
            return os.path.join(self._working_dir, 'lame.exe')
        else:
            return 'lame'


def _ensure_parent_dir(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

if __name__ == '__main__':
    if hasattr(sys, 'frozen'):
        working_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        working_dir = os.path.dirname(os.path.abspath(__file__))
    app = QtGui.QApplication(sys.argv)
    dlg = RecorderDialog(working_dir)
    dlg.show()
    sys.exit(dlg.exec_())

