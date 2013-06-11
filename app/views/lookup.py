
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import decorators, authenticate, login, logout
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect

import entry
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
    word = request.JSON['word'].strip()
    word = word_helpers.simple_correct_spelling(word)
    root_words = word_helpers.get_possible_roots(word)
    result = {
        'word': request.JSON['word'],
        'corrected_word': word,
        'dict_matches': [],
        'word_matches': [],
    }
    for root in [word] + root_words:
        match = helpers.get_first_or_none(models.Word, word=root)
        if match:
            defs = match.definitions.all()
            result['dict_matches'].append({
                'word': match.word,
                'defs': ['(%s) %s' % (x.get_part_of_speech_display(), x.english_word) \
                         for x in defs],
                'view_url': reverse(words.view_word, args=[match.word])
            })
        else:
            match = helpers.get_first_or_none(models.ExternalWord, word=root)
            if match:
                result['word_matches'].append({
                    'word': match.word,
                    'view_url': reverse(words.view_word, args=[match.word]),
                    'add_def_url': reverse(entry.enter_definition, args=[match.word]),
                })

    return result

def phrase_lookup(request):
    phrase = ''
    results = []
    if request.method == 'POST':
        phrase = request.POST['Phrase']
        phrase_words = phrase.split(' ')
        for word in phrase_words:
            word = word_helpers.simple_correct_spelling(word)

            url = ''
            pane_url = ''
            english = ''
            word_only = None

            roots = [word] + word_helpers.get_possible_roots(word)
            for root in roots:
                match = helpers.get_first_or_none(models.Word, word=root)
                if match:
                    url = reverse(words.view_word, args=[match.word])
                    pane_url = url
                    english = match.definitions.all()[:1][0].english_word
                    word_only = False

            if not english:
                for root in roots:
                    match = helpers.get_first_or_none(models.ExternalWord, word=root)
                    if match:
                        url = reverse(words.view_word, args=[match.word])
                        pane_url = helpers.get_samsad_url(match.word)
                        english = '[word only]'
                        word_only = True
            
            results.append({
                'bangla': word,
                'english': english,
                'url': url,
                'pane_url': pane_url,
                'word_only': word_only,
            })
            
    return helpers.run_template(request, 'home__phrase_lookup', {
        'phrase': phrase,
        'results': results
    })

