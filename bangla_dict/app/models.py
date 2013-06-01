from django.db import models

from django.contrib import admin
import django.contrib.auth.models as auth_models

PART_OF_SPEECH_CHOICES = (
    ('A', 'Adjective'),
    ('D', 'Adverb'),
    ('N', 'Noun'),
    ('P', 'Pronoun'),
    ('V', 'Verb')
)

class Word(models.Model):
    word = models.CharField(max_length=50, unique=True)
    added_by = models.ForeignKey(auth_models.User)
    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.word
admin.site.register(Word)

class Definition(models.Model):
    word = models.ForeignKey(Word, related_name='definitions')
    parent_word = models.ForeignKey(Word, blank=True, null=True, related_name='children')
    part_of_speech = models.CharField(max_length=2, choices=PART_OF_SPEECH_CHOICES)
    english_word = models.CharField(max_length=50)
    definition = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    added_by = models.ForeignKey(auth_models.User)
    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s (def added by %s on %s)' % (self.word.word, self.added_by,
                                               self.added_on)
admin.site.register(Definition)

class FlaggedDefinition(models.Model):
    definition = models.ForeignKey(Definition)
    reason = models.TextField()

    flagged_by = models.ForeignKey(auth_models.User)
    flagged_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s (flagged by %s on %s)' % (self.definition.word.word, self.flagged_by,
                                             self.flagged_on)
admin.site.register(FlaggedDefinition)

#class AudioRecording(models.Model):
#    word = models.ForeignKey(Word)
#    audio = models.FileField()
#
#    added_by = models.ForeignKey(auth_models.User)
#    added_on = models.DateTimeField(auto_now_add=True)

def get_automated_user(desc):
    username = '%s (automated)' % desc
    return auth_models.User.objects.get_or_create(username=username,
                                                  defaults={
                                                      'username': username,
                                                      'email': '',
                                                      'password': ''
                                                  })[0]
