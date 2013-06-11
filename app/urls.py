from django.conf.urls.defaults import patterns, include, url

import app.views.auth
import app.views.entry
import app.views.help
import app.views.home
import app.views.lookup
import app.views.words

urlpatterns = patterns('',
    (r'^$', app.views.home.index),
    (r'^word/(.+)/$', app.views.words.view_word),
    (r'^words/recently_added/$', app.views.words.recently_added),
    (r'^words/lookup/$', app.views.lookup.index),
    (r'^words/phrase_lookup/$', app.views.lookup.phrase_lookup),
    (r'^words/request_new/$', app.views.words.request_new_word),

    # Entry
    (r'^entry/new_word/$', app.views.entry.enter_new_word),
    (r'^entry/new_def/(.+)/$', app.views.entry.enter_definition), # This url is referenced in JS.
    (r'^entry/new_word_ajax/$', app.views.entry.new_word_ajax),

    # Called only by form POSTs
    (r'^words/edit_def/(\d+)/$', app.views.words.edit_def),
    (r'^words/add_def/(\d+)/$', app.views.words.add_def),

    # Called by ajax
    (r'^words/lookup/ajax/$', app.views.lookup.lookup_ajax),
    (r'^words/flag_def/$', app.views.words.flag_def),
    (r'^words/delete_def/$', app.views.words.delete_def),

    (r'^help/$', app.views.help.index),
    (r'^help/(.*)/$', app.views.help.index),

    (r'^login/$', app.views.auth.auth_login),
    (r'^login/gmail/$', app.views.auth.gmail_openid_start),
    (r'^login/gmail/return/$', app.views.auth.gmail_openid_return),
    (r'^login/facebook/$', app.views.auth.fb_oauth_start),
    (r'^login/facebook/return/$', app.views.auth.fb_oauth_return),
    (r'^signup/openid/return/$', app.views.auth.openid_finish),
    (r'^logout/$', app.views.auth.auth_logout),
    (r'^signup/$', app.views.auth.signup),
    (r'^signup/approve/(\d+)/$', app.views.auth.approve_signup),
)
