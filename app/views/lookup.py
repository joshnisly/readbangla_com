
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import decorators, authenticate, login, logout
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect

import helpers
import words

from app import models
from app import word_helpers

################################# Entrypoints
def index(request):
    if request.method == 'POST':
        if request.POST.get('Bangla'):
            return HttpResponseRedirect(reverse(words.view_word,
                                                args=[request.POST['Bangla']]))
        elif request.POST.get('English'):
            defs = models.Definition.objects.all()
            defs = defs.filter(english_word__contains=request.POST['English'])
            if len(defs):
                word_ids = set([x.word_id for x in defs])
                if len(word_ids) > 1:
                    word_matches = models.Word.objects.filter(id__in=word_ids).order_by('word')
                    return helpers.run_template(request, 'home__lookup__multiple_matches', {
                        'search_word': request.POST['English'],
                        'words': word_matches
                    })

                word = defs[0].word
                return HttpResponseRedirect(reverse(words.view_word,
                                                    args=[word.word]))
            else:
                return helpers.run_template(request, 'word_not_found', {
                    'english': request.POST['English']
                })

    return helpers.run_template(request, 'home__lookup', {
    })

@csrf_exempt
@helpers.json_entrypoint
def lookup_ajax(request):
    word = request.JSON['word']
    word = word_helpers.simple_correct_spelling(word)
    root_words = word_helpers.get_possible_roots(word)
    result = {
        'word': request.JSON['word'],
        'corrected_word': word,
        'dict_matches': [],
        'word_matches': [],
    }
    for root in [word] + root_words:
        match = _get_first_or_none(models.Word.objects.filter(word=root))
        if match:
            defs = match.definitions.all()
            result['dict_matches'].append({
                'word': match.word,
                'defs': ['(%s) %s' % (x.get_part_of_speech_display(), x.english_word) \
                         for x in defs],
                'link': reverse(words.view_word, args=[match.word])
            })
        else:
            match = _get_first_or_none(models.ExternalWord.objects.filter(word=root))
            if match:
                result['word_matches'].append(match.word)

    return result



################### Internals
def _get_first_or_none(qs):
    objs = list(qs[:1])
    if objs:
        return objs[0]
    return None
