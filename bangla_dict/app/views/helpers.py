
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template import Context, RequestContext, loader
import json
import traceback
import urllib

from app import email_send

def run_template(request, template_name, parms,
                template_file_override=None,
                template_ext='html',
                content_type=None):
    # Find this page as part of the page structure
    top, ignored, sub = template_name.partition('__')
    sub = sub.replace('_', ' ')
    top = top.replace('_', ' ')

    ua = request.META['HTTP_USER_AGENT'].lower()
    is_mobile = 'mobile' in ua or 'tablet' in ua

    template_path = template_file_override or template_name
    template = loader.get_template(template_path + '.' + template_ext)
    parms = dict(parms)
    parms.update({
        'name': template_name,
        'request': request,
    })

    template_path = template_file_override or template_name
    template = loader.get_template(template_path + '.' + template_ext)
    parms = dict(parms)
    parms['name'] = template_name
    parms['request'] = request
    parms['is_mobile'] = is_mobile
    context = RequestContext(request, parms)
    response = HttpResponse(template.render(context))
    if not content_type is None:
        response['Content-Type'] = content_type 
    return response

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

def get_first_or_none(model, **kwargs):
    objs = list(model.objects.filter(**kwargs)[:1])
    if objs:
        return objs[0]
    return None

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

