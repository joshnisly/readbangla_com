from django.contrib.auth.decorators import login_required
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
@helpers.report_errors_entrypoint
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
        if hasattr(request, 'body'):
            body = request.body
        else:
            body = request.raw_post_data

        output.write(body)

    recording = models.AudioRecording(word=word_obj, audio=full_path, added_by=request.user.get_profile())
    recording.save()

    return HttpResponse('success')
    
@helpers.report_errors_entrypoint
def download_needed(request):
    LIMIT = 100
    recently_added = models.AuditTrailEntry.objects.filter(object_name='W', action='A').order_by('-id')

    # Load words
    recently_added = [helpers.get_first_or_none(models.Word, pk=x.object_id) for x in recently_added]

    # Filter out deleted words and words that already have a recording.
    words = filter(lambda x: x and not x.audiorecording_set.count(), recently_added)

    # If we don't have enough recently added words, look at other words.
    if len(words) < LIMIT:
        words.extend(models.Word.objects.filter(audiorecording=None).order_by('word')[:LIMIT-len(words)])

    words = [x.word for x in words]
    return HttpResponse('\n'.join(words), mimetype='text/plain')

@login_required
def audio_file(request, obj_id):
    recording = models.AudioRecording.objects.get(pk=obj_id)
    audio_path = unicode(recording.audio).encode('utf8')
    body = open(audio_path, 'rb')
    response = HttpResponse(body, mimetype='audio/mpeg')
    response['Content-Length'] = os.path.getsize(audio_path)
    return response
