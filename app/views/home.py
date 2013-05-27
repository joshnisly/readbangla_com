
from django.contrib.auth import decorators, authenticate, login, logout
from django import forms
from django.http import HttpResponseRedirect

import helpers

from app import models

################################# Entrypoints
def index(request):
    return helpers.run_template(request, 'home', {
    })

# Login/logout
class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

def auth_login(request):
    error = ''
    form = LoginForm()
    next_url = ''
    if request.method == 'POST':
        next_url = request.POST['next']
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user:
                if not user.is_active:
                    error = 'Please wait for a moderator '\
                            'to enable your account.'
                else:
                    login(request, user)
                    return HttpResponseRedirect(request.POST['next'])
            else:
                error = 'Invalid username or password.'
    else:
        next_url = request.GET.get('next') or request.META.get('HTTP_REFERER')

    return helpers.run_template(request, 'login', {
        'error': error,
        'form': form,
        'next': next_url
    })

def auth_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


