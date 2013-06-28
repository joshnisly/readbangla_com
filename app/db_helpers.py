
import datetime
from django.forms.models import model_to_dict as django_mtd
import models

def remove_orphan_words():
    orphans = models.Word.objects.filter(definitions=None)
    orphans.delete()


def model_to_dict(instance):
    return django_mtd(instance)

def def_obj_to_dict(def_obj):
    def_dict = model_to_dict(def_obj)
    def_dict['added_by'] = str(def_obj.added_by)
    def_dict['added_on_date'] = datetime.datetime.strftime(def_obj.added_on, '%m/%d/%Y')
    def_dict['added_on_time'] = datetime.datetime.strftime(def_obj.added_on, '%H:%M')
    return def_dict
