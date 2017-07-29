from django.conf.urls.defaults import patterns, include, url
import os

from django.contrib import admin
admin.autodiscover()

import settings

urlpatterns = patterns('',
    (r'', include('app.urls')),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(settings.PREFIX, 'app/static')}),

    url(r'^admin/', include(admin.site.urls)),
)
