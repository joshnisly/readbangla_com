
from django.contrib.auth import decorators, authenticate, login, logout
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect

import helpers
import words

from app import models

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

