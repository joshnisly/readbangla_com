
from django.forms.models import model_to_dict as django_mtd
import models

def remove_orphan_words():
    orphans = models.Word.objects.filter(definitions=None)
    orphans.delete()


def model_to_dict(instance):
    return django_mtd(instance)
