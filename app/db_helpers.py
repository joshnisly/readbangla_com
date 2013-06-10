
import models

def remove_orphan_words():
    orphans = models.Word.objects.filter(definitions=None)
    orphans.delete()
