
from django.contrib.auth import decorators, authenticate, login, logout
from django import forms
from django.http import HttpResponseRedirect

import helpers

from app import models

################################# Entrypoints
def index(request):
    num_words = models.Word.objects.all().count()
    return helpers.run_template(request, 'home', {
        'num_words': num_words
    })



