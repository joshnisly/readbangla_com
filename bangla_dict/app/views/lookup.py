
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
    json_str = ''
    if word:
        json_str = json.dumps(_get_ajax_json_for_word_or_phrase(word))
    return helpers.run_template(request, 'home', {
        'num_words': num_words,
        'word': word,
        'parts_of_speech': json.dumps(models.PART_OF_SPEECH_CHOICES),
        'word_data': json_str
    })

@csrf_exempt
@helpers.json_entrypoint
def lookup_ajax(request):
    return _get_ajax_json_for_word_or_phrase(request.JSON['word'])

##################### Internal
def _get_ajax_json_for_word_or_phrase(input_str):
    word = input_str.strip()
    word = word_helpers.simple_correct_spelling(word)
    if ' ' in word:
        phrase_words = word.split(' ')
        result = {
            'phrase': True,
            'word': input_str,
            'word_url': reverse(index, args=[word]),
            'words': []
        }
        for phrase_word in phrase_words:
            result['words'].append(_get_json_for_word(phrase_word))

        return result

    return _get_json_for_word(input_str)
    
def _get_json_for_word(word_str):
    word = word_str.strip()
    word = word_helpers.simple_correct_spelling(word)
    root_words = word_helpers.get_possible_roots(word)
    result = {
        'word': word_str,
        'word_url': reverse(index, args=[word_str]),
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
                'edit_samsad_url': reverse(entry.edit_samsad_url, args=[match.word]),
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

    words = [x['word'] for x in result['dict_matches'] + result['word_matches']]
    if not word in words:
        result['add_def_url'] = reverse(entry.enter_definition, args=[word])

    return result

