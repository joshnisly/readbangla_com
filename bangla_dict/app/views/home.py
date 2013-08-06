from django.contrib.auth import decorators
from django.core.files.temp import NamedTemporaryFile
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse
import os

import helpers
import settings

from app import audit_trail
from app import models

def recent_changes(request):
    paginator = Paginator(models.AuditTrailEntry.objects.all().order_by('-id'), 50)

    page = request.GET.get('page', 1)
    try:
        entries = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        entries = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        entries = paginator.page(paginator.num_pages)

    changes = audit_trail.format_audit_trail_entries(entries.object_list)
    return helpers.run_template(request, 'home__recent_changes', {
        'changes': changes,
        'page': entries
    })

@helpers.http_basic_auth
def test_auth(request):
    assert request.user.is_authenticated()
    return HttpResponse('')

@decorators.login_required
def dump_db(request):
    temp_file = NamedTemporaryFile(suffix='.dump.gz')
    
    db = settings.DATABASES['default']
    MYSQL_DB = db['NAME']
    MYSQL_USERNAME = db['USER']
    MYSQL_PASSWORD = db['PASSWORD']

    command = 'mysqldump -u %s -p%s --add-drop-database --databases %s | gzip -9 > "%s"' % \
                (MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DB, temp_file.name)
    os.system(command)
    # save your data to newfile.name
    wrapper = FileWrapper(temp_file)
    response = HttpResponse(wrapper, content_type='application/gzip')
    response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(temp_file.name)
    response['Content-Length'] = os.path.getsize(temp_file.name)
    return response
