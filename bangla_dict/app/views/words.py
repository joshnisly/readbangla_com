
from django.shortcuts import get_object_or_404

import helpers

from app import models

################################# Entrypoints
def view_word(request, word_str):
    word = get_object_or_404(models.Word, word=word_str)
    return _word_entrypoint(request, word)

def view_word_by_id(request, id_):
    word = get_object_or_404(models.Word, pk=id_)
    return _word_entrypoint(request, word)

def recently_added(request):
    words = models.Word.objects.order_by('-added_on')[:100]
    return helpers.run_template(request, 'recent_words', {
        'words': words
    })

def request_new_word(request):
    assert request.method == 'POST'
    

################################ Internal
def _word_entrypoint(request, word):
    return helpers.run_template(request, 'view_word', {
        'word': word
    })
