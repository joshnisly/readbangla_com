from django.contrib.auth.decorators import login_required

from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect

import helpers
import words

from app import models
from app import word_helpers

################################# Entrypoints
@login_required
def enter_new_word(request):
    word = None
    word_form = _WordForm()
    definition_form = _DefinitionForm()
    if request.method == 'POST':
        word_form = _WordForm(request.POST)
        definition_form = _DefinitionForm(request.POST)
        if word_form.is_valid() and definition_form.is_valid():
            word_data = word_form.cleaned_data
            word = models.Word.objects.create(word=word_data['bangla_word'],
                                              added_by=request.user)
            def_data = definition_form.cleaned_data
            definition = models.Definition.objects.create(word=word,
                                  part_of_speech=def_data['part_of_speech'],
                                  english_word=def_data['english_word'],
                                  definition=def_data['definition'],
                                  notes=def_data['notes'],
                                  added_by=request.user)

            return HttpResponseRedirect(reverse(words.view_word,
                                                args=[word.word]))

    return helpers.run_template(request, 'entry__enter_new_word', {
        'word_form': word_form,
        'definition_form': definition_form,
        'word_str': None
    })

@login_required
def enter_definition(request, word_str=None):
    definition_form = _DefinitionForm()
    if request.method == 'POST':
        definition_form = _DefinitionForm(request.POST)
        if definition_form.is_valid():
            word = helpers.get_first_or_none(models.Word, word=word_str)
            if not word:
                word = models.Word.objects.create(word=word_str,
                                                  added_by=request.user)
            def_data = definition_form.cleaned_data
            definition = models.Definition.objects.create(word=word,
                                  part_of_speech=def_data['part_of_speech'],
                                  english_word=def_data['english_word'],
                                  definition=def_data['definition'],
                                  notes=def_data['notes'],
                                  added_by=request.user)

            return HttpResponseRedirect(reverse(words.view_word,
                                                args=[word.word]))

    existing_defs = []
    word = helpers.get_first_or_none(models.Word, word=word_str)
    if word:
        existing_defs = list(word.definitions.all())
    return helpers.run_template(request, 'entry__enter_new_word', {
        'definition_form': definition_form,
        'word_str': word_str,
        'existing_defs': existing_defs
    })

@helpers.json_entrypoint
def new_word_ajax(request):
    word = request.JSON['word']
    word = word_helpers.simple_correct_spelling(word)
    return {
        'word': word
    }

################################# Internals
class _WordForm(forms.Form):
    bangla_word = forms.CharField(max_length=50,
                                  widget=forms.TextInput(attrs={
                                      'class': 'Bangla'
                                  }), label='Bangla')


class _DefinitionForm(forms.Form):
    word = forms.CharField(widget=forms.HiddenInput(), required=False)
    part_of_speech = forms.CharField(widget=forms.Select(
                                     choices=models.PART_OF_SPEECH_CHOICES),
                                     initial='N')
    english_word = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
                      'title': 'Multiple words can be entered comma-separated',
                      'placeholder': 'e.g. house,home,dwelling'
                  }))
    definition = forms.CharField(required=False, widget=forms.Textarea(attrs={
                      'placeholder': '(Optional)'
                  }))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={
                      'placeholder': '(Optional)'
                  }))

