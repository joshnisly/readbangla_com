
import datetime
from django.forms.models import model_to_dict as django_mtd
import json
import time

import models

def remove_orphan_words():
    orphans = models.Word.objects.filter(definitions=None)
    orphans.delete()


def model_to_dict(instance):
    model_dict = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)
        if type(value) == datetime.datetime:
            value = time.mktime(value.timetuple())
        elif type(value) == datetime.date:
            value = int(value)
        elif type(value) == datetime.time:
            value = int(value)
        elif field.rel and value:
            value = int(value.id)

        model_dict[field.name] = value

    return model_dict

def def_obj_to_dict(def_obj):
    def_dict = model_to_dict(def_obj)
    def_dict['added_by'] = str(def_obj.added_by)
    def_dict['added_on_date'] = datetime.datetime.strftime(def_obj.added_on, '%m/%d/%Y')
    def_dict['added_on_time'] = datetime.datetime.strftime(def_obj.added_on, '%H:%M')
    return def_dict

def add_audit_trail_entry(old_record, new_record, user, user_notes=None):
    assert new_record or old_record
    if new_record and old_record:
        assert new_record.__class__ == old_record.__class__
        assert new_record.id == old_record.id
    assert user

    single_record = new_record or old_record

    class_ = single_record.__class__.__name__
    class_id = filter(lambda x: x[1] == class_, models.TABLE_IDS)
    assert class_id, 'Unsupported model'
    class_id = class_id[0][0]

    action = 'M'
    if not new_record:
        action = 'D'
    elif not old_record:
        action = 'A'

    old_record_json = json.dumps(model_to_dict(old_record)) if old_record else None
    new_record_json = json.dumps(model_to_dict(new_record)) if new_record else None
    entry = models.AuditTrailEntry(user=user, action=action,
                                   object_name=class_id,
                                   object_id=single_record.id,
                                   user_notes=user_notes,
                                   old_value_json=old_record_json,
                                   new_value_json=new_record_json)
    entry.save()

def get_first_or_none(model, **kwargs):
    objs = list(model.objects.filter(**kwargs)[:1])
    if objs:
        return objs[0]
    return None

