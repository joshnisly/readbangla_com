from django.conf.urls.defaults import patterns, include, url

import app.views.auth
import app.views.entry
import app.views.home
import app.views.lookup
import app.views.recordings
import app.views.words

urlpatterns = patterns('',
    (r'^$', app.views.lookup.index),
    (r'^lookup/(.+)/$', app.views.lookup.index),
    (r'^recent_changes/$', app.views.home.recent_changes),
    (r'^words/recently_added/$', app.views.words.recently_added),
    (r'^words/lookup/$', app.views.lookup.index),
    (r'^words/random/$', app.views.words.random),
    (r'^recordings/file/(\d+)/$', app.views.recordings.audio_file),

    (r'^dump/$', app.views.home.dump_db),


    # Entry
    (r'^entry/new_def/(.+)/$', app.views.entry.enter_definition), # This url is referenced in JS.
    (r'^entry/edit_def/(\d+)/$', app.views.entry.edit_definition),
    (r'^entry/new_word_ajax/$', app.views.entry.new_word_ajax),
    (r'^entry/edit_samsad/(.+)/$', app.views.entry.edit_samsad_url),

    # Called by ajax
    (r'^words/lookup/ajax/$', app.views.lookup.lookup_ajax),

    (r'^login/$', app.views.auth.auth_login),
    (r'^login/gmail/$', app.views.auth.gmail_openid_start),
    (r'^login/gmail/return/$', app.views.auth.gmail_openid_return),
    (r'^login/facebook/$', app.views.auth.fb_oauth_start),
    (r'^login/facebook/return/$', app.views.auth.fb_oauth_return),
    (r'^signup/openid/return/$', app.views.auth.openid_finish),
    (r'^logout/$', app.views.auth.auth_logout),
    (r'^signup/$', app.views.auth.signup),
    (r'^signup/approve/(\d+)/$', app.views.auth.approve_signup),

    # Called by recorder client
    (r'^recordings/upload/$', app.views.recordings.upload),
    (r'^recordings/needed_words/$', app.views.recordings.download_needed),
    (r'^test_auth/$', app.views.home.test_auth),
)
