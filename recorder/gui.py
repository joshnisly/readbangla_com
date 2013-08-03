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
        parser.add_section('Settings')
        for setting, value in self._values.items():
            parser.set('Settings', setting.lower(), value)
        with open(self._path, 'w') as output_file:
            parser.write(output_file)


    def get_setting(self, setting, default=None):
        return self._values.get(setting.lower(), default)

    def set_setting(self, setting, value):
        self._values[setting.lower()] = value

class RecorderDialog(QtGui.QDialog):
    def __init__(self, working_dir, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle(self.tr('Bangla Recorder Client'))

        self._is_playing = False
        self._working_dir = working_dir

        self._remaining_words = []

        self._settings = Settings(os.path.join(self._working_dir, 'settings.ini'))

        self._temp_path = os.path.join(self._working_dir, 'temp', 'working.wav')
        _ensure_parent_dir(self._temp_path)
        self._message_queue = Queue.Queue()
        self._recorder = recording.Recorder(self._temp_path, self)
        self._uploader = uploading.Uploader(self, self._settings.get_setting('host', _DEFAULT_HOST),
                                            self._settings.get_setting('port', _DEFAULT_PORT),
                                            self._settings.get_setting('username', ''),
                                            self._settings.get_setting('password', ''))

        self._silence_level = int(self._settings.get_setting('threshold', 0))
        self._recorder.set_threshold(self._silence_level)

        self._error_to_display = None
        self._status_text = None
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

        self._status_label = QtGui.QLabel('Ready.')
        full_layout.addWidget(self._status_label)

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

        # Queue un-uploaded files
        outbox_path = os.path.join(self._working_dir, 'outbox')
        for entry in os.listdir(outbox_path):
            entry = unicode(entry, 'utf8')
            word = os.path.splitext(entry)[0]
            self._uploader.add_item(os.path.join(outbox_path, entry), word)

    def reject(self):
        self._recorder.quit()
        self._uploader.quit()
        QtGui.QDialog.reject(self)

    def on_error(self, error):
        self._error_to_display = error

    def on_status_update(self, status):
        self._status_text = status

    def _display_error(self):
        if self._error_to_display:
            QtGui.QMessageBox.critical(self, 'Error', self._error_to_display)
            self._error_to_display = None

        if self._status_text:
            self._status_label.setText(self._status_text)
            self._status_text = None

    def on_recording_finish(self):
        self._update_ui()

    def _download(self):
        try:
            response = helpers.request_with_auth(self._settings.get_setting('host', _DEFAULT_HOST),
                                                 self._settings.get_setting('port', _DEFAULT_PORT),
                                                 '/recordings/needed_words/',
                                                 self._settings.get_setting('username', ''),
                                                 self._settings.get_setting('password', ''))
            self._remaining_words = response.split('\n')
        except Exception, e:
            self.on_error(e.message)

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
        if self._silence_level == 0:
            QtGui.QMessageBox.critical(self, 'Calibration required', 'You must calibrate the software before recording.')
            return

        self._recorder.start_stop()
        self._update_ui()

    def _play_back(self):
        if not os.path.exists(self._temp_path):
            QtGui.QMessageBox.critical(self, 'Error', 'Please record a word first.')
            return

        self._is_playing = True
        self._update_ui()
        play.play_wav(self._temp_path)
        self._is_playing = False
        self._update_ui()

    def _convert_and_upload(self):
        try:
            if not os.path.exists(self._temp_path):
                QtGui.QMessageBox.critical(self, 'Error', 'Please record a word before uploading.')
                return

            cur_word = self._get_cur_word()

            # Convert to MP3
            lame_path = self._get_lame_path()
            os.system(u'%s -mm -h %s %s' % (lame_path, self._temp_path, self._temp_path + '.mp3'))

            target_path = os.path.join(self._working_dir, 'outbox', cur_word + '.mp3')
            _ensure_parent_dir(target_path)
            os.rename(self._temp_path + '.mp3', target_path)

            self._uploader.add_item(target_path, cur_word)

            os.unlink(self._temp_path)
            self._remaining_words = self._remaining_words[1:]
            self._update_ui(True)
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

        self._silence_level = int(self._recorder.get_90th_percentile() * 1.1)
        msg = 'Silence calibration complete\nSound level: %i.' % self._silence_level
        response = QtGui.QMessageBox.information(self, 'Calibration, part 1', msg)
        self._recorder.set_threshold(self._silence_level)
        self._settings.set_setting('threshold', str(self._silence_level))
        self._settings.save()
        
    def _get_lame_path(self):
        if os.name == 'nt':
            return os.path.join(self._working_dir, 'lame.exe')
        else:
            return 'lame'

class SettingsDialog(QtGui.QDialog):
    def __init__(self, settings_path):
        QtGui.QDialog.__init__(self, None)

        self._settings_path = settings_path

        username_layout = QtGui.QHBoxLayout()
        username_label = QtGui.QLabel('Username:')
        username_layout.addWidget(username_label)
        self._username_edit = QtGui.QLineEdit()
        self._username_edit.setMinimumWidth(200)
        username_layout.addWidget(self._username_edit)

        password_layout = QtGui.QHBoxLayout()
        password_label = QtGui.QLabel('Password:')
        password_layout.addWidget(password_label)
        self._password_edit = QtGui.QLineEdit()
        self._password_edit.setMinimumWidth(200)
        password_layout.addWidget(self._password_edit)

        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.addStretch()
        self._ok_button = QtGui.QPushButton('&OK')
        self.connect(self._ok_button, QtCore.SIGNAL('clicked()'), self.accept)
        buttons_layout.addWidget(self._ok_button)
        self._cancel_button = QtGui.QPushButton('&Cancel')
        self.connect(self._cancel_button, QtCore.SIGNAL('clicked()'), self.reject)
        buttons_layout.addWidget(self._cancel_button)

        self._full_layout = QtGui.QVBoxLayout()
        self._full_layout.addLayout(username_layout)
        self._full_layout.addLayout(password_layout)
        self._full_layout.addLayout(buttons_layout)
        self.setLayout(self._full_layout)


    def accept(self):
        username = str(self._username_edit.text())
        password = str(self._password_edit.text())

        try:
            helpers.request_with_auth(_DEFAULT_HOST, _DEFAULT_PORT, '/test_auth/',
                                      username, password)
        except helpers.BadAuth, e:
            QtGui.QMessageBox.critical(self, 'Invalid Credentials', str(e))
        except Exception, e:
            QtGui.QMessageBox.critical(self, 'Unknown Error', unicode(e.message))
        else:
            settings = Settings(self._settings_path)
            settings.set_setting('username', username)
            settings.set_setting('password', password)
            settings.save()

            QtGui.QDialog.accept(self)


def _ensure_parent_dir(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

_DEFAULT_HOST = 'www.readbangla.com'
_DEFAULT_PORT = '80'

if __name__ == '__main__':
    if hasattr(sys, 'frozen'):
        working_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        working_dir = os.path.dirname(os.path.abspath(__file__))

    app = QtGui.QApplication(sys.argv)

    settings_path = os.path.join(working_dir, 'settings.ini')
    if not os.path.exists(settings_path):
        dlg = SettingsDialog(settings_path)
        if dlg.exec_() != QtGui.QDialog.Accepted:
            sys.exit(0)

    dlg = RecorderDialog(working_dir)
    dlg.show()
    sys.exit(dlg.exec_())

