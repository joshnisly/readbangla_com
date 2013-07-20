from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import helpers

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
