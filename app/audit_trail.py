import datetime
import difflib
from django.core.urlresolvers import reverse
import json

import models

import views.lookup

def get_def_modify_entries(def_obj):
    entries = models.AuditTrailEntry.objects.filter(object_id=def_obj.id, action='M', object_name='D')
    return entries.order_by('-id')

def format_audit_trail_entries(entries):
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
                deletion_entry = models.AuditTrailEntry.objects.get(object_name='W',
                                                                    object_id=single_obj['word'],
                                                                    action='D')
                word_str = json.loads(deletion_entry.old_value_json)['word']
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
            entry_dict['url'] = reverse(views.lookup.index, args=[word_str])
        entry_dict['action'] = entry.action
        entry_dict['object_name'] = entry.object_name
        entry_dict['action_desc'] = u'%s %s' % (_action_desc(entry.action), changes_desc)
        entry_dict['word'] = word_str or '<deleted word>'
        entry_dict['old'] = old_obj
        entry_dict['new'] = new_obj
        entry_dict['single'] = single_obj
        entry_dict['added_by'] = models.UserProfile.objects.get(pk=single_obj['added_by'])
        entry_dict['added_on'] = datetime.datetime.fromtimestamp(single_obj['added_on']).strftime('%m/%d/%Y %I:%M %P')

        # Generate diff for modified definition
        if entry.object_name == 'D' and entry.action == 'M':
            def lines_from_def(obj):
                return [
                    'Part of speech: ' + models.get_part_of_speech_display(obj['part_of_speech']),
                    'English: ' + obj['english_word'],
                    'Definition: ' + obj['definition'],
                    'Notes: ' + obj['notes']
                ]
            old_lines = lines_from_def(old_obj)
            new_lines = lines_from_def(new_obj)

            differ = difflib.HtmlDiff()
            entry_dict['diff'] = differ.make_table(old_lines, new_lines, 'Old', 'New', context=False)
        

        change_dicts.append(entry_dict)

    return change_dicts

def record_user_word_lookup(user, word_str):
    models.UserLookupTrail.objects.create(user=user.get_profile(), word=word_str)

def _format_timedelta(td):
    years = int(td.days / 365)
    hours = int(td.seconds / 60 / 60)
    minutes = int((td.seconds % (60 * 60)) / 60)
    seconds = int(td.seconds % 60)
    days = td.days - (years * 365)
    
    descs = [
        _get_desc('year', years),
        _get_desc('day', days),
        _get_desc('hour', hours),
        _get_desc('minute', minutes),
        _get_desc('second', seconds)
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
