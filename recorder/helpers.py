#!/usr/bin/python

import httplib
import urllib

#HOST = 'www.readbangla.com'
HOST = 'localhost'
#PORT = '80'
PORT = '8000'

def request_with_auth(path, username, password, query_parms=None, post_data=None):
    conn = httplib.HTTPConnection(HOST, PORT)
    headers = {}
    if username:
        assert password

        auth = '%s:%s' % (username, password)
        headers['Authorization'] = 'Basic ' + auth.encode('base64')

    if query_parms is not None:
        path = path + '?' + urllib.urlencode(query_parms)

    conn.request('POST' if post_data else 'GET', path, body=post_data, headers=headers)
    response = conn.getresponse()
    if response.status != 200:
        raise ValueError, 'Invalid response: ' + response.read().decode('utf8')

    return response.read().decode('utf8')
