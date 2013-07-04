
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
import urllib

import helpers
import lookup

from app import models

################################# Entrypoints
def recently_added(request):
    words = models.Word.objects.order_by('-added_on')[:100]
    return helpers.run_template(request, 'home__recently_added', {
        'words': words
    })

def random(request):
    word = models.Word.objects.order_by('?')[0]
    return HttpResponseRedirect(reverse(lookup.index, args=[word.word]))

