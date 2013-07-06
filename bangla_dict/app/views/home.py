
import datetime
from django.contrib.auth import decorators, authenticate, login, logout
from django import forms
from django.http import HttpResponseRedirect
import json

import helpers

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
                word_str = '<deleted word>'
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
        #entry_dict['url'] = entry.get_url()
        entry_dict['action'] = entry.action
        entry_dict['action_desc'] = u'%s %s %s' % (_action_desc(entry.action), changes_desc, word_str)
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
    if years > 0:
        return '%i years, %i days' % (years, td.days)
    elif td.days > 0:
        return '%i days, %i hours' % (td.days, hours)
    elif td.seconds > 60 * 60:
        return '%i hours, %i minutes' % (hours, minutes)
    elif minutes > 0:
        return '%i minutes' % minutes
    else:
        return '%i seconds' % td.seconds

def _action_desc(action_id):
    if action_id == 'M':
        return 'modified'
    elif action_id == 'A':
        return 'added'
    elif action_id == 'D':
        return 'deleted'
