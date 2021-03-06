
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template import Context, RequestContext, loader
import json
import traceback
import urllib

from app import email_send
from app import db_helpers
from app import word_helpers

def run_template(request, template_name, parms,
                template_file_override=None,
                template_ext='html',
                content_type=None):
    content = get_template_content(request, template_name, parms,
                                   template_file_override, template_ext)
    response = HttpResponse(content)
    if not content_type is None:
        response['Content-Type'] = content_type 
    return response

def get_template_content(request, template_name, parms,
                         template_file_override=None,
                         template_ext='html'):
    ua = request.META['HTTP_USER_AGENT'].lower()
    is_mobile = 'mobile' in ua or 'tablet' in ua

    template_path = template_file_override or template_name
    template = loader.get_template(template_path + '.' + template_ext)
    parms = dict(parms)
    parms.update({
        'name': template_name,
        'request': request,
        'is_mobile': is_mobile,
        'global_spelling_corrections': json.dumps(word_helpers.SIMPLE_SPELLING_CORRECTIONS)
    })

    context = RequestContext(request, parms)
    return template.render(context)

def send_email(to_list, subject, parms, template_name, cc=[], bcc=[], replyto=None):
    template = loader.get_template(template_name + '.txt')
    context = Context(parms)
    email_text = template.render(context)
    email_send.send_email(to_list, subject, email_text, cc, bcc, replyto)

def json_entrypoint(func):
    def wrap(request, *a, **kw):
        try:
            body = request.body
        except AttributeError:
            body = request.raw_post_data
        request.JSON = json.loads(body)
        try:
            response = func(request, *a, **kw)
        except Exception, e:
            response = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        else:
            if isinstance(response, HttpResponse):
                return response

        json_str = json.dumps(response)
        return HttpResponse(json_str, mimetype='text/javascript')
    return wrap

def report_errors_entrypoint(func):
    def wrap(request, *a, **kw):
        try:
            return func(request, *a, **kw)
        except Exception, e:
            res = HttpResponse(traceback.format_exc(), mimetype='text/plain')
            res.status_code = 500
            return res
    return wrap

def http_basic_auth(func):
    def wrap(request, *a, **kw):
        auth = request.META.get('HTTP_AUTHORIZATION')
        if auth:
            method, auth = auth.split(' ', 1)
            if method.lower() == 'basic':
                auth = auth.strip().decode('base64')
                username, password = auth.split(':', 1)
                user = authenticate(username=username, password=password)
                if user and user.is_active:
                    request.user = user
                    return func(request, *a, **kw)
                    
        res = HttpResponse('Authorization Required', mimetype='text/plain')
        res['WWW-Authenticate'] = 'Basic realm="BanglaDict"'
        res.status_code = 401
        return res

    return wrap

def get_first_or_none(model, **kwargs):
    return db_helpers.get_first_or_none(model, **kwargs)

def get_samsad_url_for_word_obj(word_obj):
    keyword = word_obj.samsad_keyword or word_obj.word
    url = 'http://dsalsrv02.uchicago.edu/cgi-bin/romadict.pl?table=biswas-bengali&query='
    url += urllib.quote_plus(keyword.encode('utf-8'))
    if word_obj.samsad_entries_only:
        url += '&searchhws=yes'
    if word_obj.samsad_exact_match:
        url += '&matchtype=exact'

    return url

            
def get_samsad_url(word):
    return 'http://dsalsrv02.uchicago.edu/cgi-bin/romadict.pl?query=%s&searchhws=yes&table=biswas-bengali' % \
            urllib.quote_plus(word.encode('utf-8'))

