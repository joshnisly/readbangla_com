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
def enter_new_word(request, new_word_id=None):
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
        'word': word
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
                                        choices=models.PART_OF_SPEECH_CHOICES))
    english_word = forms.CharField(max_length=50)
    definition = forms.CharField(widget=forms.Textarea(), required=False)
    notes = forms.CharField(widget=forms.Textarea(), required=False)

