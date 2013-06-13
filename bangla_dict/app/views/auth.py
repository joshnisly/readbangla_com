from django.core.urlresolvers import reverse
from django.contrib.auth import decorators, authenticate, login, logout
from django.contrib.auth.models import User
from django import forms
from django.http import HttpResponseForbidden, HttpResponseRedirect
import urllib
import urlparse

import facebook
import openid.extensions.ax # pylint: disable-msg=F0401
from openid.consumer import consumer # pylint: disable-msg=F0401

import helpers
import settings

############################ Login/logout
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
        if form.is_valid() and form.cleaned_data['password'] != ' ':
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
        next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/'
        request.session['next'] = next_url

    return helpers.run_template(request, 'login', {
        'error': error,
        'form': form,
        'next': next_url
    })

def auth_logout(request):
    logout(request)
    return HttpResponseRedirect('/')

def gmail_openid_start(request):
    openid_parms = {}
    con = consumer.Consumer(openid_parms, None)

    # Get openid_request
    openid_request = con.begin(_GMAIL_URL)

    # Setup AttributeExchange (ax) to get the user email address
    ax_request = openid.extensions.ax.FetchRequest()
    ax_request.add(openid.extensions.ax.AttrInfo(_AX_EMAIL_URL, alias='email',
                                                 required=True))
    ax_request.add(openid.extensions.ax.AttrInfo(_AX_FIRST_NAME_URL, alias='first_name',
                                                 required=True))
    ax_request.add(openid.extensions.ax.AttrInfo(_AX_LAST_NAME_URL, alias='last_name',
                                                 required=True))
    openid_request.addExtension(ax_request)

    # Get redirect url
    realm = request.build_absolute_uri('/')
    return_url = request.build_absolute_uri(reverse(gmail_openid_return))
    redirect_url = openid_request.redirectURL(return_to=return_url, realm=realm)

    return HttpResponseRedirect(redirect_url)


def gmail_openid_return(request):
    con = consumer.Consumer({}, None)
    this_url = request.build_absolute_uri(reverse(gmail_openid_return))
    openid_response = con.complete(request.POST or request.GET, this_url)
    
    if openid_response.status == consumer.SUCCESS:
        ax_response = openid.extensions.ax.FetchResponse()
        ax_response = ax_response.fromSuccessResponse(openid_response)
        email = ax_response.get(_AX_EMAIL_URL)[0]
        first_name = ax_response.get(_AX_FIRST_NAME_URL)[0]
        last_name = ax_response.get(_AX_LAST_NAME_URL)[0]
        return _on_verify_email(request, email, first_name, last_name)

    return HttpResponseRedirect(reverse(auth_login))

def openid_finish(request):
    if request.method != 'POST':
        return HttpResponseRedirect('/')
    assert request.session['email']
    form = _SignupOpenIDForm(request.POST)
    if form.is_valid():
        user = User(username=request.session['email'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=request.session['email'],
                    is_active=False,
                    is_superuser=False)
        user.set_password(' ')
        user.save()
        _send_signup_email(request, {
            'first_name': form.cleaned_data['first_name'],
            'last_name': form.cleaned_data['last_name'],
            'email': request.session['email'],
            'user_id': user.id,
        })
        return helpers.run_template(request, 'signup_success', {})

    return helpers.run_template(request, 'signup_openid', {
        'form': form
    })


### Facebook stuff
def fb_oauth_start(request):
    return_url = request.build_absolute_uri(reverse(fb_oauth_return))
    fb_url = _FB_OAUTH_URL + '&redirect_uri=' + urllib.quote_plus(return_url)
    return HttpResponseRedirect(fb_url)

def fb_oauth_return(request):
    if 'error_message' in request.GET:
        return helpers.run_template(request, 'error', {
            'message': 'Unable to log in: ' + request.GET['error_message']
        })
    elif 'code' in request.GET:
        code = request.GET['code']

        redirect_uri = request.build_absolute_uri(reverse(fb_oauth_return))
        access_token = facebook.get_access_token_from_code(code, redirect_uri,
                                                           _FB_APP_ID,
                                                           _FB_APP_SECRET)['access_token']
        graph = facebook.GraphAPI(access_token)
        user = graph.get_object('me')
        return _on_verify_email(request, user['email'], first_name=user['first_name'],
                                last_name=user['last_name'])
    else:
        return helpers.run_template(request, 'error', {
            'message': 'An unexpected error occurred.'
        })



############################ Signup
def signup(request):
    form = _SignupForm()
    if request.method == 'POST':
        form = _SignupForm(request.POST)
        if form.is_valid():
            user = User(username=form.cleaned_data['email'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        email=form.cleaned_data['email'],
                        is_active=False,
                        is_superuser=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            _send_signup_email(request, {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                'user_id': user.id,
            })
            return helpers.run_template(request, 'signup_success', {})

    return helpers.run_template(request, 'signup', {'form': form})

@decorators.login_required
def approve_signup(request, user_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden('')
    user_id = int(user_id)
    user = User.objects.get(pk=user_id)
    if not user.is_active:
        user.is_active = True
        user.save()
        admin_emails = [x[1] for x in settings.ADMINS]
        helpers.send_email([user.email], 'Membership Approved', {
                              'user': user,
                              'host': settings.HOST
                          }, 'signup_approved_email', bcc=admin_emails)
    return helpers.run_template(request, 'signup_approved', {'new_user': user})

######################################################################
def _on_verify_email(request, email, first_name=None, last_name=None):
    # See if this user has already signed up.
    users = User.objects.filter(username=email)
    if len(users):
        assert len(users) == 1
        user = users[0]
        if not user.is_active:
            error = 'Please wait for a moderator to enable your account.'
            return helpers.run_template(request, 'error', {
                'message': error
            })
        else:
            user = authenticate(username=email, password=' ')
            if not user:
                error = 'There is a password assigned to this account.' + \
                        'Please log in with that password.'
                return helpers.run_template(request, 'error', {
                    'message': error
                })
            login(request, user)
        return HttpResponseRedirect(request.session.get('next', '/'))

    else:
        request.session['email'] = email
        if first_name or last_name:
            initial = {
                'first_name': first_name or '',
                'last_name': last_name or ''
            }
            form = _SignupOpenIDForm(initial)
        else:
            form = _SignupOpenIDForm()
        return helpers.run_template(request, 'signup_openid', {
            'form': form
        })

def _send_signup_email(request, parms):
    parms = dict(parms)
    parms['remote_ip'] = request.META['REMOTE_ADDR']
    parms['host'] = settings.HOST

    admin_emails = [x[1] for x in settings.ADMINS]
    helpers.send_email(admin_emails, 'Signup Request', parms, 'signup_email')

class _SignupForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_pw = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        # Make sure passwords match
        if 'password' in self.cleaned_data and \
                'confirm_pw' in self.cleaned_data:
            if self.cleaned_data['password'] != \
                    self.cleaned_data['confirm_pw']:

                self._errors['password'] = \
                    forms.util.ErrorList(['Passwords do not match.'])

                del self.cleaned_data['password']
                del self.cleaned_data['confirm_pw']
        return self.cleaned_data

class _SignupOpenIDForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)

_GMAIL_URL = 'https://www.google.com/accounts/o8/id'
_AX_EMAIL_URL = 'http://axschema.org/contact/email'
_AX_FIRST_NAME_URL = 'http://axschema.org/namePerson/first'
_AX_LAST_NAME_URL = 'http://axschema.org/namePerson/last'

_FB_APP_ID = '460019804088843'
_FB_APP_SECRET = '5a2928997b7994fba9f81258ce7e905b'
_FB_OAUTH_URL = 'https://www.facebook.com/dialog/oauth/?client_id=%s&scope=email' % _FB_APP_ID

