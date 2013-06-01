
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect
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
    return helpers.run_template(request, 'home__recently_added', {
        'words': words
    })

@login_required
def request_new_word(request):
    assert request.method == 'POST'
    
@login_required
def edit_def(request, def_id):
    assert request.method == 'POST'

    word_def = get_object_or_404(models.Definition, pk=def_id)
    assert word_def.added_by == request.user or request.user.is_superuser

    form = DefinitionForm(request.POST, instance=word_def)
    if not form.is_valid():
        print form.errors
        assert False
    form.save()
    return HttpResponseRedirect(reverse(view_word, args=[word_def.word.word]))

@login_required
@helpers.json_entrypoint
def flag_def(request):
    assert request.method == 'POST'
    def_id = request.JSON['def_id']
    word_def = get_object_or_404(models.Definition, pk=def_id)

    models.FlaggedDefinition.objects.create(definition=word_def,
                                            reason=request.JSON['reason'],
                                            flagged_by=request.user)

    return {'success': True}

@login_required
@helpers.json_entrypoint
def delete_def(request):
    assert request.method == 'POST'
    return {}


################################ Internal
def _word_entrypoint(request, word):
    definitions = word.definitions.all()
    if request.user.is_authenticated:
        definitions = []
        for definition in word.definitions.all():
            definitions.append({
                'form': DefinitionForm(instance=definition),
                'definition': definition
            })
    return helpers.run_template(request, 'view_word', {
        'word': word,
        'definitions': definitions
    })

class DefinitionForm(forms.ModelForm):
    class Meta:
        model = models.Definition
        exclude = ('word', 'added_by', 'added_on')
