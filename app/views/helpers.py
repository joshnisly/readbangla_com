
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template import Context, RequestContext, loader



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

