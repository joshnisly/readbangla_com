
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

import helpers
import lookup

from app import models

################################# Entrypoints
def recently_added(request):
    words = models.Word.objects.order_by('-added_on')[:100]
    return helpers.run_template(request, 'home__recently_added', {
        'words': words
    })

def random(request):
    word = models.Word.objects.order_by('?')[0]
    return HttpResponseRedirect(reverse(lookup.index, args=[word.word]))

def browse(request, current_letter=None):
    wordstrs = models.Word.objects.select_related('definition')
    words_by_letter = groupby(wordstrs, lambda x: x.word[0])

    if not current_letter in words_by_letter:
        current_letter = u'\u0985'

    letter_words = words_by_letter[current_letter]
    return helpers.run_template(request, 'browse_words', {
        'letters': sorted(words_by_letter.keys()),
        'words': sorted(letter_words, key=lambda x: x.word),
        'current_letter': current_letter
    })


class groupby(dict):
    def __init__(self, seq, key=lambda x:x):
        for value in seq:
            k = key(value)
            self.setdefault(k, []).append(value)
    __iter__ = dict.iteritems

