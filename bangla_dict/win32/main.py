#!/usr/bin/python

import re
import time
import urllib
import webbrowser
import win32clipboard

CF_UNICODETEXT = 13

def launch_text(text):
    text = re.sub('[()\r\n]', '', text)
    url_text = urllib.quote(text.encode('utf8'))
    if ' ' in text:
        url = 'http://bangla.joshnisly.com/words/phrase_lookup/%s/' % url_text
    else:
        url = 'http://bangla.joshnisly.com/word/%s/' % url_text
    webbrowser.open(url)


last_text = ''
while True:
    try:
        win32clipboard.OpenClipboard()
        bangla = win32clipboard.GetClipboardData(CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
    except Exception:
        continue

    if bangla == last_text:
        continue

    last_text = bangla

    for char in bangla:
        if char >= u'\u0981' and char <= u'\u09FF':
            launch_text(bangla)
            break

    time.sleep(0.25)

