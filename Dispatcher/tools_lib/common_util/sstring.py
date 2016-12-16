#!/usr/bin/env python
# @Date    : 2016-02-29 11:27:03
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo

# Fake unicode literal support:  Python 3.2 doesn't have the u'' marker for
# literal strings, and alternative solutions like "from __future__ import
# unicode_literals" have other problems (see PEP 414).  u() can be applied
# to ascii strings that include \u escapes (but they must not contain
# literal non-ascii characters).

if not isinstance(b'', type('')):
    def u(s):
        return s


    unicode_type = str
    basestring_type = str
else:
    def u(s):
        return s.decode('unicode_escape')


    # These names don't exist in py3, so use noqa comments to disable
    # warnings in flake8.
    unicode_type = unicode  # noqa
    basestring_type = basestring  # noqa

_UTF8_TYPES = (bytes, type(None))


def safe_utf8(value):
    """Converts a string argument to a byte string.

    If the argument is already a byte string or None, it is returned unchanged.
    Otherwise it must be a unicode string and is encoded as utf8.
    """
    if isinstance(value, _UTF8_TYPES):
        return value
    if not isinstance(value, unicode_type):
        return value
        # raise TypeError(
        #     "Expected bytes, unicode, or None; got %r" % type(value)
        # )
    return value.encode("utf-8")


def safe_unicode(value):
    if isinstance(value, unicode_type):
        return value
    if isinstance(value, _UTF8_TYPES):
        return value.decode('utf-8')

    return value


def convert_utf8(value):
    if isinstance(value, _UTF8_TYPES):
        return value
    if isinstance(value, unicode_type):
        return value.encode("utf-8")
    return str(value)


def safe_format(format_str, *arg, **kwargs):
    safe_arg = [safe_utf8(s) for s in arg]
    safe_kwargs = {safe_utf8(k): safe_utf8(v) for k, v in kwargs.iteritems()}
    safe_str = safe_utf8(format_str)
    return safe_str.format(*safe_arg, **safe_kwargs)


def safe_join(iterable, separator='\t'):
    safe_iterable = [convert_utf8(v) for v in iterable]
    safe_sep = safe_utf8(separator)
    return safe_sep.join(safe_iterable)
