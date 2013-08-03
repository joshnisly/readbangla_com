#!/usr/bin/python

import httplib
import urllib

class BadAuth(Exception):
    pass

def request_with_auth(host, port, path, username, password, query_parms=None, post_data=None):
    conn = httplib.HTTPConnection(host, int(port))
    headers = {}
    if username:
        assert password

        auth = '%s:%s' % (username, password)
        headers['Authorization'] = 'Basic ' + auth.encode('base64')

    if query_parms is not None:
        path = path + '?' + urllib.urlencode(query_parms)

    conn.request('POST' if post_data else 'GET', path, body=post_data, headers=headers)
    response = conn.getresponse()
    if response.status == 401:
        raise BadAuth, 'Invalid username or password.'
    if response.status != 200:
        raise ValueError, 'Invalid response: ' + response.read().decode('utf8')

    return response.read().decode('utf8')
