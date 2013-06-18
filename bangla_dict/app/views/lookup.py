
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import decorators, authenticate, login, logout
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect
import json

import entry
import helpers
import words

from app import models
from app import db_helpers
from app import word_helpers

################################# Entrypoints
def index(request, word=None):
    num_words = models.Word.objects.all().count()
    return helpers.run_template(request, 'home', {
        'num_words': num_words,
        'word': word,
        'parts_of_speech': json.dumps(models.PART_OF_SPEECH_CHOICES)
    })

@csrf_exempt
@helpers.json_entrypoint
def lookup_ajax(request):
    word = request.JSON['word'].strip()
    if ' ' in word:
        phrase_words = word.split(' ')
        result = {
            'phrase': True,
            'word': request.JSON['word'],
            'words': []
        }
        for phrase_word in phrase_words:
            result['words'].append(_get_json_for_word(phrase_word))

        return result

    return _get_json_for_word(request.JSON['word'])


def phrase_lookup(request, phrase_text=None):
    if not phrase_text and request.method == 'POST':
        phrase_text = request.POST['Phrase']

    phrase = ''
    results = []
    if phrase_text:
        phrase_words = phrase_text.split(' ')
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
        'phrase': phrase_text or '',
        'results': results
    })

##################### Internal
def _get_json_for_word(word_str):
    word = word_str.strip()
    word = word_helpers.simple_correct_spelling(word)
    root_words = word_helpers.get_possible_roots(word)
    result = {
        'word': word_str,
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
                'defs': [db_helpers.model_to_dict(x) for x in defs],
                'view_url': reverse(index, args=[match.word]),
                'samsad_url': helpers.get_samsad_url(match.word),
                'add_def_url': reverse(entry.enter_definition, args=[match.word]),
            })
        else:
            match = helpers.get_first_or_none(models.ExternalWord, word=root)
            if match:
                result['word_matches'].append({
                    'word': match.word,
                    'view_url': reverse(index, args=[match.word]),
                    'add_def_url': reverse(entry.enter_definition, args=[match.word]),
                    'samsad_url': helpers.get_samsad_url(match.word),
                })

    return result

