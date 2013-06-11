#!/usr/bin/python

import codecs
import os
import re
import sys
import unittest

PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
path = os.path.dirname(os.path.dirname(PARENT_DIR))
sys.path.insert(0, path)

import django.core.management

import settings
django.core.management.setup_environ(settings)

import django.db
import django.db.transaction
from django.contrib.auth.models import User

from app import db_helpers
from app import models
from app.views import helpers

USER = models.get_automated_user('KM-words')

PARTS_OF_SPEECH = {
    'adj.': 'A',
    'adj': 'A',
    'adv.': 'D',
    'adv': 'D',
    'name': 'O',
    'noun': 'N',
    'prep.': 'R',
    'verb': 'V',
}

def _split_with_quotes(s, delim):
    results = []
    while True:
        in_quotes = False
        for i in range(0, len(s)):
            if s[i] == '"':
                in_quotes = not in_quotes
            elif s[i] == delim and not in_quotes:
                result = s[:i].strip('"')
                results.append(result)
                s = s[i+1:]
                break
        else:
            results.append(s.strip('"'))
            return results

@django.db.transaction.commit_manually
def convert(input_path, debug):
    total_added = 0
    skipped = 0

    try:
        # Clean out old words
        old_defs = models.Definition.objects.filter(added_by=USER)
        old_defs.delete()
        db_helpers.remove_orphan_words()
        django.db.transaction.commit()

        for line in open(input_path).readlines()[1:]:
            parts = _split_with_quotes(line.strip(), ',')
            word = dict(zip(['id', 'word', 'def', 'type', 'pronunciation'], parts))

            if not word['def']:
                continue

            if not word['type']:
                skipped += 1
                if debug:
                    print 'Skipping word %s due to no part of speech...' % word['id']
                continue

            types = [word['type']]
            defs = [word['def']]
            if '/' in word['type']:
                types = [x.strip() for x in word['type'].split('/')]
                assert len(types) == 2
                if '/' in defs:
                    defs = [x.strip() for x in word['def'].split('/')]
                    assert len(defs) == 2
                else:
                    defs = defs + defs
                
            for type_, def_ in zip(types, defs):
                if not type_ in PARTS_OF_SPEECH:
                    skipped += 1
                    if debug:
                        print 'Skipping word %s (%s) due to unrecognized part of speech...' % (word['word'], word['def'])
                    continue

                word_notes = ''
                if word['pronunciation']:
                    word_notes = 'Pronunciation: ' + word['pronunciation']

                long_def = ''
                if len(def_) > 100:
                    long_def = def_
                    def_ = def_[:50] + '...'

                word_obj = models.Word.objects.get_or_create(word=word['word'], defaults={'added_by': USER})[0]
                models.Definition.objects.create(word=word_obj, 
                                                 part_of_speech=PARTS_OF_SPEECH[type_],
                                                 english_word=def_,
                                                 notes=word_notes,
                                                 added_by=USER)

                total_added += 1
                if total_added % 500 == 0:
                    print '%s...' % total_added
                    django.db.transaction.commit()


        django.db.transaction.commit()
        print 'Imported: %i' % total_added
        print 'Skipped: %i' % skipped
    except BaseException:
        django.db.transaction.rollback()
        raise




############################# Tests
class SplitTests(unittest.TestCase):
    def test(self):
        self._test(u'4332,"\u09B8\u09AE\u09C2\u09B9","collection, totality, number, sum","noun",',
                   [u'4332', u'\u09B8\u09AE\u09C2\u09B9', u'collection, totality, number, sum', u'noun', u''])
        self._test(u'4332,,,,',
                   [u'4332', u'', u'', u'', u''])
        self._test(u'4332,,,,"test"',
                   [u'4332', u'', u'', u'', u'test'])


    def _test(self, s, results):
        self.assertEquals(_split_with_quotes(s, ','), results)

if __name__ == '__main__':
    if '--test' in sys.argv:
        sys.argv.remove('--test')
        unittest.main()
    else:
        convert(os.path.abspath('data.csv'), '--debug' in sys.argv)

