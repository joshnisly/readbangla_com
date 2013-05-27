from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django import forms

import os
import re

import helpers

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))), 'docs')

def index(request, name=None):
    name = name or 'index'
    markup = open(os.path.join(DOCS_DIR, name.replace(' ', '_') + '.txt')).read()
    content = _munger_markup(markup)
    return helpers.run_template(request, 'help__index', {
        'content': content,
        'title': 'Help - %s' % name
    })

def _munger_markup(markup):
    mutators = [
        # Headings
        ('===(.*?)===', lambda x: '<h3>' + x.group(1) + '</h3>'),
        ('==(.*?)==', lambda x: '<h2>' + x.group(1) + '</h2>'),
        ('=(.*?)=', lambda x: '<h1>' + x.group(1) + '</h1>'),
        # Links
        ('\[\[(.*?)\]\]', lambda x: _render_link(x.group(1))),
        # Bold/italic
        ("'''(.*?)'''", lambda x: '<b>' + x.group(1) + '</b>'),
        ("''(.*?)''", lambda x: '<em>' + x.group(1) + '</em>'),
        # Lists
        # Ordered
        ("(^1.*?)(^[^1])", lambda x: '<ol>\n' + x.group(1) + '</ol>' + x.group(2), re.S|re.M),
        ("^1(.*)", lambda x: '<li>' + x.group(1) + '</li>', re.M),
        # Bulleted
        ("(^\*.*?)(^[^*])", lambda x: '<ul>\n' + x.group(1) + '</ul>' + x.group(2), re.S|re.M),
        ("^\*(.*)", lambda x: '<li>' + x.group(1) + '</li>', re.M),
        #("^([^*])", lambda x: 'line start' + x.group(1) + ''),
        
        # Newlines
        ('\n(\n+)', lambda x: '<br/>\n' * len(x.group(1))),

    ]

    for mutator in mutators:
        regex, replace_fn = mutator[0:2]
        flags = 0
        if len(mutator) > 2:
            flags = mutator[2]
        reg = re.compile(regex, flags)
        markup = reg.sub(replace_fn, markup)

    return markup

def _render_list_part(match, part_name):
    pass

def _render_link(link_spec):
    link_parts = link_spec.split('|')
    page = link_parts[0]
    title = page
    if len(link_parts) > 1 and link_parts[1]:
        title = link_parts[1]

    url = reverse(index, args=[page])
    return '<a href="%s">%s</a>' % (url, title)

