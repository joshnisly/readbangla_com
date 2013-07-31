from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import os
import random
import string

import settings
import helpers

from app import audit_trail
from app import models

@csrf_exempt
@helpers.http_basic_auth
def upload(request):
    assert request.user
    assert request.method == 'POST'

    word = request.GET['word']
    word_obj = helpers.get_first_or_none(models.Word, word=word)
    if word_obj is None:
        return HttpResponse('This word does not exist.', status=500, mimetype='text/plain')

    random_chars = ''.join(random.sample(string.letters+string.digits, 8))

    name = u'%s_%s.mp3' % (word, random_chars)
    full_path = os.path.join(settings.PREFIX, 'audio_files', name.encode('utf8'))
    if not os.path.exists(os.path.dirname(full_path)):
        os.makedirs(os.path.dirname(full_path))
    with open(full_path, 'wb') as output:
        output.write(full_path)

    recording = models.AudioRecording(word=word_obj, audio=full_path, added_by=request.user.get_profile())
    recording.save()

    return HttpResponse('success')
    
def download_needed(request):
    limit = 100
    recently_added = models.AuditTrailEntry.objects.filter(object_name='W', action='A').order_by('-id')
    recently_added = [helpers.get_first_or_none(models.Word, pk=x.object_id) for x in recently_added]
    recently_added = filter(lambda x: x and not x.audiorecording_set.count(), recently_added)

    words = [x.word for x in recently_added]
    return HttpResponse('\n'.join(words), mimetype='text/plain')
