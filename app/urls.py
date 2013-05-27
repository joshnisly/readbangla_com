from django.conf.urls.defaults import patterns, include, url

import app.views.entry
import app.views.home
import app.views.lookup
import app.views.words

urlpatterns = patterns('',
    (r'^$', app.views.home.index),
    (r'^entry/new_word/$', app.views.entry.enter_new_word),
    (r'^word/id/(\d+)/$', app.views.words.view_word_by_id),
    (r'^word/(.+)/$', app.views.words.view_word),
    (r'^words/recently_added/$', app.views.words.recently_added),
    (r'^words/lookup/$', app.views.lookup.index),
    (r'^words/request_new/$', app.views.words.request_new_word),

    (r'^login/$', app.views.home.auth_login),
    (r'^logout/$', app.views.home.auth_logout),
)
