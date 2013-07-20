
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import decorators, authenticate, login, logout
from django.core.urlresolvers import reverse
from django.db.models import Q
from django import forms
from django.http import HttpResponseRedirect
import json

import entry
import helpers
import words

from app import audit_trail
from app import db_helpers
from app import models
from app import word_helpers

################################# Entrypoints
def index(request, word=None):
    num_words = models.Word.objects.all().count()
    json_str = ''
    is_english = False
    if word:
        json_obj = _get_ajax_json_for_word_or_phrase(request, word)
        json_str = json.dumps(json_obj)
        is_english = json_obj['is_english']

    return helpers.run_template(request, 'home', {
        'num_words': num_words,
        'word': word,
        'parts_of_speech': json.dumps(models.PART_OF_SPEECH_CHOICES),
        'word_data': json_str,
        'is_english': is_english
    })

@csrf_exempt
@helpers.json_entrypoint
def lookup_ajax(request):
    return _get_ajax_json_for_word_or_phrase(request, request.JSON['word'])

##################### Internal
def _get_ajax_json_for_word_or_phrase(request, input_str):
    word = word_helpers.simple_correct_spelling(input_str)
    word = word.strip()
    if ' ' in word:
        phrase_words = word.split(' ')
        result = {
            'phrase': True,
            'word': input_str,
            'word_url': reverse(index, args=[word]),
            'words': [],
            'is_english': False
        }
        for phrase_word in phrase_words:
            if phrase_word.strip():
                result['words'].append(_get_json_for_word(request, phrase_word))

        return result

    return _get_json_for_word(request, input_str)

def _get_json_for_word(request, word_str):
    word = word_str.strip()
    if word and word_helpers.is_ascii(word):
        return _get_json_for_english_word(request, word_str)

    word = word_helpers.simple_correct_spelling(word)
    root_words = word_helpers.get_possible_roots(word)
    result = {
        'word': word_str,
        'word_url': reverse(index, args=[word_str]),
        'corrected_word': word,
        'dict_matches': [],
        'word_matches': [],
        'is_english': False
    }
    for root in [word] + root_words:
        match = helpers.get_first_or_none(models.Word, word=root)
        if match:
            result['dict_matches'].append({
                'word': match.word,
                'defs': [_get_def_dict(request, x) for x in match.definitions.all()],
                'view_url': reverse(index, args=[match.word]),
                'samsad_url': helpers.get_samsad_url_for_word_obj(match),
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

def _get_json_for_english_word(request, raw_word):
    word = raw_word.strip()
    dict_matches = models.Definition.objects.filter(Q(english_word__icontains=word) |
                                                    Q(definition__icontains=word) |
                                                    Q(notes__icontains=word)).select_related('word')
    matches = {}
    for match in dict_matches:
        matches.setdefault(match.word, []).append(match)
        
    result = {
        'word': raw_word,
        'word_url': reverse(index, args=[word]),
        'corrected_word': word,
        'dict_matches': [],
        'word_matches': [],
        'is_english': True
    }

    for word in matches:
        result['dict_matches'].append({
            'word': word.word,
            'defs': [_get_def_dict(request, x) for x in matches[word]],
            'view_url': reverse(index, args=[word.word]),
            'samsad_url': helpers.get_samsad_url_for_word_obj(word),
            'edit_samsad_url': reverse(entry.edit_samsad_url, args=[word.word]),
            'add_def_url': reverse(entry.enter_definition, args=[word.word]),
        })
    return result

def _get_def_dict(request, def_obj):
    def_dict = db_helpers.def_obj_to_dict(def_obj)
    def_dict['edit_def_url'] = reverse(entry.edit_definition,
                                       args=[def_dict['id']])

    #def_dict['edits'] = 
    edits = audit_trail.format_audit_trail_entries(audit_trail.get_def_modify_entries(def_obj))
    def_dict['num_edits'] = len(edits)
    def_dict['edits_html'] = helpers.get_template_content(request, 'changes_table', {
        'changes': edits
    })
    return def_dict

