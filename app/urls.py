from django.conf.urls.defaults import patterns, include, url

import app.views.entry
import app.views.help
import app.views.home
import app.views.lookup
import app.views.words

urlpatterns = patterns('',
    (r'^$', app.views.home.index),
    (r'^entry/new_word/$', app.views.entry.enter_new_word),
    (r'^word/(.+)/$', app.views.words.view_word),
    (r'^words/recently_added/$', app.views.words.recently_added),
    (r'^words/lookup/$', app.views.lookup.index),
    (r'^words/request_new/$', app.views.words.request_new_word),

    # Called only by form POSTs
    (r'^words/edit_def/(\d+)/$', app.views.words.edit_def),
    (r'^words/add_def/(\d+)/$', app.views.words.add_def),

    # Called by ajax
    (r'^words/flag_def/$', app.views.words.flag_def),
    (r'^words/delete_def/$', app.views.words.delete_def),

    (r'^help/$', app.views.help.index),
    (r'^help/(.*)/$', app.views.help.index),


    (r'^login/$', app.views.home.auth_login),
    (r'^logout/$', app.views.home.auth_logout),
)
