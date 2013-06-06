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

def _isascii(text):
    try:
        text.decode('ascii')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False
    else:
        return True

@django.db.transaction.commit_manually
def process_file(file_path):
    input_file = codecs.open(file_path, 'rb', encoding='utf16')

    try:
        cursor = django.db.connection.cursor()
        cursor.execute('DELETE from app_externalword')

        total_added = 0
        for line in input_file.readlines():
            if not line.strip() or line.startswith('#'):
                continue

            if line.startswith('\t'):
                continue

            line = line.strip()
            if not _isascii(line):
                existing_words = models.ExternalWord.objects.filter(word=line)
                if not existing_words.count():
                    total_added += 1
                    models.ExternalWord.objects.create(word=line)
                    if total_added % 500 == 0:
                        print '%s...' % total_added
                        django.db.transaction.commit()

        django.db.transaction.commit()
        print total_added, 'total'
    except BaseException:
        django.db.transaction.rollback()
        raise

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Usage: %s <input file>' % sys.argv[0]
        sys.exit(1)

    process_file(sys.argv[1])

