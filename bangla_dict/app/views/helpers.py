
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template import Context, RequestContext, loader
import json

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

    init_links = _get_page_structure()
    links = []
    sub_links = []
    for link in init_links:
        if not is_mobile or len(link) >= 5:
            links.append(link)
        if top == link[0].lower():
            sub_links = link[2]

    template_path = template_file_override or template_name
    template = loader.get_template(template_path + '.' + template_ext)
    parms = dict(parms)
    parms.update({
        'name': template_name,
        'request': request,
        'top_links': links,
        'top_link_name': top,
        'sub_links': sub_links,
        'sub_link_name': sub
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
            response = {'error': str(e)}
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

############################### Internals
def _get_page_structure():
    return (
        ('Home', '/', [
            ('Lookup', reverse('app.views.lookup.index')),
            ('Recently Added', reverse('app.views.words.recently_added')),
        ], None, True),
        #('Scheduling', reverse('app.views.scheduling.month_view'), [], 'Scheduling (Horiaro)', True),
        ('Entry', reverse('app.views.entry.enter_new_word'), [
            ('Enter New Word', reverse('app.views.entry.enter_new_word')),
            ('Enter New Definition', reverse('app.views.entry.enter_new_word')),
        ]),
        ('Help', reverse('app.views.help.index'), []),
    )

