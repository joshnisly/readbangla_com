
import datetime
from django.core.urlresolvers import reverse
from django.contrib.auth import decorators, authenticate, login, logout
from django import forms
from django.http import HttpResponseRedirect
import json

import helpers
import lookup

from app import models

def recent_changes(request):
    entries = models.AuditTrailEntry.objects.all().order_by('-id')[:100]

    change_dicts = []
    for entry in entries:
        old_obj = json.loads(entry.old_value_json) if entry.old_value_json else None
        new_obj = json.loads(entry.new_value_json) if entry.new_value_json else None
        single_obj = new_obj or old_obj

        if entry.object_name == 'D':
            changes_desc = 'a definition for'
            try:
                word_str = models.Word.objects.get(pk=single_obj['word'])
            except Exception:
                word_str = None
        elif entry.object_name == 'W' and entry.action == 'M' and \
                (old_obj['samsad_keyword'] != new_obj['samsad_keyword'] or \
                old_obj['samsad_entries_only'] != new_obj['samsad_entries_only'] or \
                old_obj['samsad_exact_match'] != new_obj['samsad_exact_match']):
            changes_desc = 'the samsad link for'
            word_str = (new_obj or old_obj)['word']
        else:
            continue

        entry_dict = {}
        entry_dict['user'] = str(entry.user)
        if entry.date:
            entry_dict['date'] = entry.date.strftime('%m/%d/%Y %I:%M:%S %P')
            entry_dict['time_since'] = _format_timedelta(datetime.datetime.now() - entry.date)
        if word_str:
            entry_dict['url'] = reverse(lookup.index, args=[word_str])
        entry_dict['action'] = entry.action
        entry_dict['action_desc'] = u'%s %s' % (_action_desc(entry.action), changes_desc)
        entry_dict['word'] = word_str or '<deleted word>'
        entry_dict['old'] = old_obj
        entry_dict['new'] = new_obj

        change_dicts.append(entry_dict)
    return helpers.run_template(request, 'home__recent_changes', {
        'changes': change_dicts
    })


def _format_timedelta(td):
    years = int(td.days / 365)
    hours = int(td.seconds / 60 / 60)
    minutes = int((td.seconds % (60 * 60)) / 60)
    
    descs = [
        _get_desc('year', years),
        _get_desc('day', td.days),
        _get_desc('hour', hours),
        _get_desc('minute', minutes),
        _get_desc('second', td.seconds)
    ]
    descs = filter(lambda x: x, descs)
    return ', '.join(descs[:2]) or 'a few seconds'

def _get_desc(str_, num):
    if not num:
        return ''
    if num == 1:
        return '1 ' + str_
    else:
        return '%i %ss' % (num, str_)

def _action_desc(action_id):
    if action_id == 'M':
        return 'modified'
    elif action_id == 'A':
        return 'added'
    elif action_id == 'D':
        return 'deleted'
