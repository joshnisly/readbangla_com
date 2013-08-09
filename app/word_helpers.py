
import re

NO_PUNCTUATION_RE = re.compile('[|,;"\'-]')

SIMPLE_SPELLING_CORRECTIONS = [
    (u'\ufeff', ''), # UTF8 BOM
    (u'\u0985\u09BE', u'\u0986'),
    (u'\u09AF\u09BC', u'\u09DF'),
    (u'\u09A1\u09BC', u'\u09DC'),
]

def simple_correct_spelling(word):
    corrections = list(SIMPLE_SPELLING_CORRECTIONS)
    corrections.append((u'\u0964', '')) # | to end sentences

    for bad, good in corrections:
        word = word.replace(bad, good)

    word = NO_PUNCTUATION_RE.sub(' ', word)
    return word.strip(' ')


def get_possible_roots(word):
    roots = []

    # Try removing off a bunch of suffixes (order is important!)
    suffixes = [
        u'\u0995\u09c7', # "ke"
        u'\u09A6\u09C7\u09B0', # "der"
        u'\u09C7\u09B0\u09BE', # "era"
        u'\u09B0', # "r"
    ]
    for suffix in suffixes:
        if word.endswith(suffix):
            word = word[:-len(suffix)]
            roots.append(word)

    return roots

def is_ascii(text):
    try:
        text.decode('ascii')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False
    else:
        return True

