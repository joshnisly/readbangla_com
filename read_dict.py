#!/usr/bin/python

import codecs
import re
import sys

import django.core.management
import settings
django.core.management.setup_environ(settings)

from app import models
from django.contrib.auth.models import User
import django.db
import django.db.transaction

MY_USER = models.get_automated_user('samsad')

DEF1_REGEX = re.compile('\[m1\](.*?)\[/m\]')
TAGS_REGEX = re.compile('\[.*?\](.*?)\[/.*?\]')
BAD_TAGS_REGEX = re.compile('\[.*?\]')

TYPE_MAPPING = {
    'a': 'A',
    'adv': 'D',
    'n': 'N',
    'v': 'V',
    'pro': 'P',
}

total_lines = 0

def _isascii(text):
    try:
        text.decode('ascii')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False
    else:
        return True

def process_entry(entry_lines, def_lines):
    entry_lines = [x.strip() for x in entry_lines]
    def_lines = [x.strip() for x in def_lines]

    entry = entry_lines[0]
    if entry == 'version':
        return

    english_words = filter(lambda x: _isascii(x), entry_lines)

    #print entry
    english_word = ','.join(english_words)

    def_ = None
    for line in def_lines:
        match = DEF1_REGEX.search(line)
        if match:
            def_ = match.group(1)
            break

    def_ = TAGS_REGEX.sub('\\1', def_)
    def_ = BAD_TAGS_REGEX.sub('', def_)
    def_ = def_.lstrip('~ -')
    type_, ignored, def_ = def_.partition('.')

    if not type_ in TYPE_MAPPING:
        return

    words = models.Word.objects.filter(word=entry)
    if words:
        word = words[0]
    else:
        word = models.Word.objects.create(word=entry, added_by=MY_USER)

    definition = models.Definition.objects.create(word=word,
                                                  english_word=english_word,
                                                  definition=def_,
                                                  part_of_speech=TYPE_MAPPING[type_],
                                                  parent_word=None,
                                                  added_by=MY_USER)

    global total_lines
    total_lines = total_lines + 1
    if total_lines % 500 == 0:
        django.db.transaction.commit()
    print entry.encode('ascii', 'replace'), def_.encode('ascii', 'replace')

@django.db.transaction.commit_manually
def process_file(file_path):
    input_file = codecs.open(file_path, 'rb', encoding='utf16')

    try:
        cursor = django.db.connection.cursor()
        cursor.execute('DELETE from app_word')
        cursor.execute('DELETE from app_definition')

        in_def = False

        entry_lines = []
        def_lines = []
        for line in input_file.readlines():
            if not line.strip() or line.startswith('#'):
                continue

            if line.startswith('\t'):
                in_def = True
                def_lines.append(line.lstrip('\t'))
                continue

            if in_def:
                in_def = False
                process_entry(entry_lines, def_lines)
                entry_lines = []
                def_lines = []

            entry_lines.append(line)

        process_entry(entry_lines, def_lines)
        django.db.transaction.commit()
    except BaseException:
        django.db.transaction.rollback()
        raise

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Usage: %s <input file>' % sys.argv[0]
        sys.exit(1)

    process_file(sys.argv[1])
