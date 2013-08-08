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

    AUDIO_DIR = os.path.join(settings.PREFIX, 'audio_files')
    TEMP_WAV_PATH = os.path.join(AUDIO_DIR, 'wav', random_chars + '.wav')
    TEMP_MP3_PATH = os.path.join(AUDIO_DIR, 'mp3', random_chars + '.mp3')
    TEMP_OGG_PATH = os.path.join(AUDIO_DIR, 'ogg', random_chars + '.ogg')

    for path in [TEMP_WAV_PATH, TEMP_MP3_PATH, TEMP_OGG_PATH]:
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

    # WAV file
    with open(TEMP_WAV_PATH, 'wb') as output:
        if hasattr(request, 'body'):
            body = request.body
        else:
            body = request.raw_post_data

        # Terrible hack to work around bugs in Django's standalone server.
        body = body.lstrip('\r\n')
        output.write(body)

    # Convert to mp3
    os.system(u'lame -mm -h %s %s' % (TEMP_WAV_PATH, TEMP_MP3_PATH))

    # Convert to ogg
    os.system(u'oggenc -q3 -C1 -o %s %s' % (TEMP_OGG_PATH, TEMP_WAV_PATH))

    title = u'%s_%s' % (word, random_chars)
    WAV_PATH = os.path.join(AUDIO_DIR, 'wav', title + '.wav')
    os.rename(TEMP_WAV_PATH.encode('utf8'), WAV_PATH.encode('utf8'))
    MP3_PATH = os.path.join(AUDIO_DIR, 'mp3', title + '.mp3')
    os.rename(TEMP_MP3_PATH.encode('utf8'), MP3_PATH.encode('utf8'))
    OGG_PATH = os.path.join(AUDIO_DIR, 'ogg', title + '.ogg')
    os.rename(TEMP_OGG_PATH.encode('utf8'), OGG_PATH.encode('utf8'))

    recording = models.AudioRecording(word=word_obj,
                                      wav=WAV_PATH,
                                      mp3=MP3_PATH,
                                      ogg=OGG_PATH,
                                      added_by=request.user.get_profile())
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
    if request.GET.get('type') == 'ogg':
        audio_path = unicode(recording.ogg).encode('utf8')
        mimetype = 'audio/ogg'
    else:
        audio_path = unicode(recording.mp3).encode('utf8')
        mimetype = 'audio/mpeg'
    body = open(audio_path, 'rb')
    response = HttpResponse(body, mimetype=mimetype)
    response['Content-Length'] = os.path.getsize(audio_path)
    return response
