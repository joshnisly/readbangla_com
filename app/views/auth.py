from django import forms
from django.contrib.auth import decorators, authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, HttpResponseRedirect


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
        next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/'

    return helpers.run_template(request, 'login', {
        'error': error,
        'form': form,
        'next': next_url
    })

def auth_logout(request):
    logout(request)
    return HttpResponseRedirect('/')

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
            admin_emails = [x[1] for x in settings.ADMINS]
            helpers.send_email(admin_emails, 'Signup Request', {
                                  'first_name': form.cleaned_data['first_name'],
                                  'last_name': form.cleaned_data['last_name'],
                                  'email': form.cleaned_data['email'],
                                  'user_id': user.id,
                                  'remote_ip': request.META['REMOTE_ADDR'],
                                  'host': settings.HOST
                              }, 'signup_email')
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


class _SignupForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_pw = forms.CharField(widget=forms.PasswordInput)
    reason = forms.CharField(max_length=200, required=False)

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


