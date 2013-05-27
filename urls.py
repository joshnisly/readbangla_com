from django.conf.urls.defaults import patterns, include, url
import os

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import settings

urlpatterns = patterns('',
    (r'', include('bangla_dict.app.urls')),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(settings.PREFIX, 'app/static')}),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
