"""
====================
Facebook API Support
====================

This module provides support for accessing the Facebook API.

Assuming a pair of API/Secret keys from Facebook, the ``call`` and ``validator``
functions can be initialised:

  >>> from nodeconfig import FACEBOOK_API_KEY, FACEBOOK_SECRET_KEY

  >>> call, validate = create_facebook_handlers(
  ...     FACEBOOK_API_KEY, FACEBOOK_SECRET_KEY
  ... )

The ``call`` function can be used to access all available Facebook API calls.
The API function name is the first parameter and can be followed by relevant
keyword arguments.

For example, to access ``users.GetInfo`` for a given UID, one can do:

  >>> dataset = call('users.GetInfo', uids='593997068', fields='name')

Since we asked for just one UID, the result should only have a single item:

  >>> len(dataset)
  1

And, within that it should have a dictionary containing the data we want:

  >>> info = dataset[0]

  >>> info['name']
  u'Tav Espian'

  >>> info['uid']
  593997068

"""

from hashlib import md5
from time import time
from urllib import urlencode
from urllib2 import urlopen

import json

# ------------------------------------------------------------------------------
# some konstants
# ------------------------------------------------------------------------------

FACEBOOK_URL = "http://api.facebook.com/restserver.php?"
FACEBOOK_VERSION = "1.0"

# ------------------------------------------------------------------------------
# kore funktion
# ------------------------------------------------------------------------------

def create_facebook_handlers(api_key, secret):
    """Return functions to call and validate Facebook API methods."""

    def call(method, **kwargs):

        kwargs.update({
            'api_key': api_key,
            'call_id': time() * 10000,
            'format': 'JSON',
            'method': method,
            'v': FACEBOOK_VERSION
            })

        hash = md5(''.join('%s=%s' % (k, kwargs[k]) for k in sorted(kwargs)))
        hash.update(secret)

        kwargs['sig'] = hash.hexdigest()

        data = json.loads(urlopen(FACEBOOK_URL+urlencode(kwargs)).read())

        if 'error_code' in data:
            raise TypeError("%(error_code)s: %(error_msg)s" % data)

        return data

    def validate(**kwargs):

        signature = kwargs.pop('fb_sig')

        hash = md5(''.join('%s=%s' % (k[7:], kwargs[k]) for k in sorted(kwargs)))
        hash.update(secret)

        return signature == hash.hexdigest()

    return call, validate
