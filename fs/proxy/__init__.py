# coding: utf-8

import pkg_resources
import email

try:
    dist = pkg_resources.get_distribution(__name__)
    info = email.message_from_string(dist.get_metadata(dist.PKG_INFO))
except Exception:
    dist = None
    info = None
else:
    __version__ = dist.version
    __author__ = '{} <{}>'.format(info['Author'], info['Author-email'])
    __license__ = 'Copyright (c) 2017 {}'.format(info['Author'])
finally:
    del dist
    del info
    del email
    del pkg_resources
