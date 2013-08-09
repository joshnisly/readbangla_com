from django.contrib.auth.decorators import login_required

from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect

import helpers
import lookup
import words

from app import db_helpers
from app import models
from app import word_helpers

################################# Entrypoints
@login_required
def enter_definition(request, word_str=None):
    return _run_edit_def_entrypoint(request, word_str)

@login_required
def edit_definition(request, def_id):
    def_obj = helpers.get_first_or_none(models.Definition, id=def_id)
    if not def_obj:
        return HttpResponseRedirect(reverse(lookup.index))

    word_str = def_obj.word.word
    return _run_edit_def_entrypoint(request, word_str, def_obj)

@login_required
def edit_samsad_url(request, word_str):
    word = helpers.get_first_or_none(models.Word, word=word_str)
    if not word:
        return HttpResponseRedirect(reverse(lookup.index, args=[word_str]))

    if request.method == 'POST' and request.POST.get('Action') == 'Submit':
        raw_keyword = request.POST['Keyword']
        word.samsad_keyword = raw_keyword if raw_keyword != word.word else ''
        word.samsad_entries_only = 'EntriesOnly' in request.POST
        word.samsad_exact_match = 'ExactMatch' in request.POST
        old_word = models.Word.objects.get(pk=word.id)
        db_helpers.add_audit_trail_entry(old_word, word, request.user.get_profile())
        word.save()

        return HttpResponseRedirect(reverse(lookup.index, args=[word.word]))

    if request.method == 'POST' and request.POST.get('Action') == 'Cancel':
        return HttpResponseRedirect(reverse(lookup.index, args=[word.word]))
        
    return helpers.run_template(request, 'entry__edit_samsad_url', {
        'word': word,
        'keyword': word.samsad_keyword or word.word
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
                      'placeholder': 'e.g. home'
                  }))
    definition = forms.CharField(required=False, widget=forms.Textarea(attrs={
                      'placeholder': '(Optional) e.g. house, home, dwelling'
                  }))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={
                      'placeholder': u'(Optional) e.g. Typically used for '+\
                                     u'a permanent home. See also \u09AC\u09BE\u09B8\u09BE.'
                  }))

def _run_edit_def_entrypoint(request, word_str, def_obj=None):
    if def_obj:
        definition_form = _DefinitionForm(initial={
            'part_of_speech': def_obj.part_of_speech,
            'english_word': def_obj.english_word,
            'definition': def_obj.definition,
            'notes': def_obj.notes,
        })
    else:
        definition_form = _DefinitionForm()
    if request.method == 'POST' and request.POST.get('Action') == 'Delete':
        db_helpers.add_audit_trail_entry(def_obj, None, request.user.get_profile())
        def_obj.delete()

        if not def_obj.word.definitions.all().count():
            db_helpers.add_audit_trail_entry(def_obj.word, None, request.user.get_profile())
            def_obj.word.delete()
            return HttpResponseRedirect(reverse(lookup.index))
        else:
            return HttpResponseRedirect(reverse(lookup.index,
                                                args=[def_obj.word.word]))

    if request.method == 'POST' and request.POST.get('Action') == 'Edit':
        definition_form = _DefinitionForm(request.POST)
        if definition_form.is_valid():
            word = helpers.get_first_or_none(models.Word, word=word_str)
            is_new_word = False
            if not word:
                word = models.Word.objects.create(word=word_str, added_by=request.user.get_profile())
                db_helpers.add_audit_trail_entry(None, word, request.user.get_profile())
                is_new_word = True
            def_data = definition_form.cleaned_data
            def_args = {
                'part_of_speech': def_data['part_of_speech'],
                'english_word': def_data['english_word'],
                'definition': word_helpers.simple_correct_spelling(def_data['definition']),
                'notes': word_helpers.simple_correct_spelling(def_data['notes']),
            }
            if def_obj:
                for key, value in def_args.items():
                    def_obj.__setattr__(key, value)

                old_def = models.Definition.objects.get(pk=def_obj.id)
                db_helpers.add_audit_trail_entry(old_def, def_obj, request.user.get_profile())
                def_obj.save()
            else:
                new_def = models.Definition.objects.create(word=word,
                                                           added_by=request.user.get_profile(),
                                                           **def_args)
                db_helpers.add_audit_trail_entry(None, new_def, request.user.get_profile())

            # If this is the first definition for the word, redirect to the Edit Samsad page.
            if is_new_word:
                return HttpResponseRedirect(reverse(edit_samsad_url, args=[word.word]))
            else:
                return HttpResponseRedirect(reverse(lookup.index, args=[word.word]))

    existing_defs = []
    word = helpers.get_first_or_none(models.Word, word=word_str)
    if word:
        existing_defs = list(word.definitions.all())
        if def_obj:
            existing_defs = filter(lambda x: x.id != def_obj.id, existing_defs)

    return helpers.run_template(request, 'entry__enter_new_word', {
        'definition_form': definition_form,
        'word_str': word_str,
        'existing_defs': existing_defs,
        'is_existing_def': def_obj is not None
    })

