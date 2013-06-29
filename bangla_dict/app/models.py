from django.db import models

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
import django.contrib.auth.models as auth_models
from django.db.models.signals import post_save

PART_OF_SPEECH_CHOICES = (
    ('N', 'Noun'),
    ('V', 'Verb'),
    ('A', 'Adjective'),
    ('D', 'Adverb'),
    ('P', 'Pronoun'),
    ('C', 'Conjunction'),
    ('R', 'Preposition'),
    ('O', 'Proper noun'),
)

class UserProfile(models.Model):
    user = models.ForeignKey(auth_models.User, unique=True) 

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

def on_user_save(sender, instance, **kwargs):
    profile, new = UserProfile.objects.get_or_create(user=instance)
post_save.connect(on_user_save, sender=auth_models.User)

class ProfileInline(admin.StackedInline):
    model = UserProfile
    fields = ('user',)
    extra = 0

class ProfileUserAdmin(UserAdmin):
    inlines = [ProfileInline]

#admin.site.unregister(auth_models.User)
#admin.site.register(auth_models.User, ProfileUserAdmin)


class Word(models.Model):
    word = models.CharField(max_length=50, unique=True)
    added_by = models.ForeignKey(UserProfile)
    added_on = models.DateTimeField(auto_now_add=True)

    samsad_keyword = models.CharField(max_length=100)
    samsad_entries_only = models.BooleanField()
    samsad_exact_match = models.BooleanField()

    def __unicode__(self):
        return self.word
admin.site.register(Word)

class Definition(models.Model):
    word = models.ForeignKey(Word, related_name='definitions')
    parent_word = models.ForeignKey(Word, blank=True, null=True, related_name='children')
    part_of_speech = models.CharField(max_length=2, choices=PART_OF_SPEECH_CHOICES)
    english_word = models.CharField(max_length=100)
    definition = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    added_by = models.ForeignKey(UserProfile)
    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s (def added by %s on %s)' % (self.word.word, self.added_by,
                                               self.added_on)

admin.site.register(Definition)

class FlaggedDefinition(models.Model):
    definition = models.ForeignKey(Definition)
    reason = models.TextField()

    flagged_by = models.ForeignKey(UserProfile)
    flagged_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s (flagged by %s on %s)' % (self.definition.word.word, self.flagged_by,
                                             self.flagged_on)
admin.site.register(FlaggedDefinition)

# This table is for word lists that we don't have permission to use for 
# definitions, but can just as a simple word list.
class ExternalWord(models.Model):
    word = models.CharField(max_length=50, unique=True)

    def __unicode__(self):
        return self.word

admin.site.register(ExternalWord)

def get_automated_user(desc):
    username = '%s_automated' % desc
    user = auth_models.User.objects.get_or_create(username=username,
                                                  defaults={
                                                      'username': username,
                                                      'email': '',
                                                      'password': '',
                                                      'first_name': desc,
                                                      'last_name': '(automated)',
                                                  })[0]
    return user.get_profile()
