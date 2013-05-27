from django.db import models

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

class Definition(models.Model):
    word = models.ForeignKey(Word, related_name='definitions')
    parent_word = models.ForeignKey(Word, blank=True, null=True, related_name='children')
    part_of_speech = models.CharField(max_length=2, choices=PART_OF_SPEECH_CHOICES)
    english_word = models.CharField(max_length=50)
    definition = models.TextField()
    notes = models.TextField()

    added_by = models.ForeignKey(auth_models.User)
    added_on = models.DateTimeField(auto_now_add=True)


#class AudioRecording(models.Model):
#    word = models.ForeignKey(Word)
#    audio = models.FileField()
#
#    added_by = models.ForeignKey(auth_models.User)
#    added_on = models.DateTimeField(auto_now_add=True)
