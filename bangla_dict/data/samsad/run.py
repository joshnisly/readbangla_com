#!/usr/bin/python

import codecs
import os
import re
import sys

PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
path = os.path.dirname(os.path.dirname(PARENT_DIR))
sys.path.insert(0, path)

import django.core.management

import settings
django.core.management.setup_environ(settings)

import django.db
import django.db.transaction
from django.contrib.auth.models import User

from app import models

def _isascii(text):
    try:
        text.decode('ascii')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False
    else:
        return True

@django.db.transaction.commit_manually
def process_file(file_path, debug):
    input_file = codecs.open(file_path, 'rb', encoding='utf16')

    try:
        cursor = django.db.connection.cursor()
        cursor.execute('DELETE from app_externalword')

        total_added = 0
        skipped = 0
        for line in input_file.readlines():
            if not line.strip() or line.startswith('#'):
                continue

            if line.startswith('\t'):
                continue

            line = line.strip()
            if ' ' in line:
                if debug:
                    print 'Skipping %s' % line
                skipped += 1
                continue

            if not _isascii(line):
                existing_words = models.ExternalWord.objects.filter(word=line)
                if not existing_words.count():
                    total_added += 1
                    models.ExternalWord.objects.create(word=line)
                    if total_added % 500 == 0:
                        print '%s...' % total_added
                        django.db.transaction.commit()

        django.db.transaction.commit()
        print 'Imported: %i' % total_added
        print 'Skipped: %i' % skipped
    except BaseException:
        django.db.transaction.rollback()
        raise

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        input_path = sys.argv[1]
    else:
        input_name = 'samsad.dsl'
        input_path = os.path.join(PARENT_DIR, input_name)
        if not os.path.exists(input_path):
            assert os.path.exists(input_path + '.gz')
            os.system('gunzip -c %s.gz > %s' % (input_name, input_name))

    print 'Import Samsad wordlist into ExternalWord table...'
    process_file(input_path, '--debug' in sys.argv)

