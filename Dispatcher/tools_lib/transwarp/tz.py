#!/usr/bin/env python
# coding:utf-8
import re
import datetime

_TIMEDELTA_ZERO = datetime.timedelta(0)

# timezone as UTC+8:00, UTC-10:00
_RE_TZ = re.compile('^([\+\-])([0-9]{1,2})\:([0-9]{1,2})$')


class UTC(datetime.tzinfo):
    """
    A UTC tzinfo object.

    >>> tz0 = UTC('+00:00')
    >>> tz0.tzname(None)
    'UTC+00:00'
    >>> tz8 = UTC('+8:00')
    >>> tz8.tzname(None)
    'UTC+8:00'
    >>> tz7 = UTC('+7:30')
    >>> tz7.tzname(None)
    'UTC+7:30'
    >>> tz5 = UTC('-05:30')
    >>> tz5.tzname(None)
    'UTC-05:30'
    >>> import datetime
    >>> u = datetime.datetime.utcnow().replace(tzinfo=tz0)
    >>> l1 = u.astimezone(tz8)
    >>> l2 = u.replace(tzinfo=tz8)
    >>> d1 = u - l1
    >>> d2 = u - l2
    >>> d1.seconds
    0
    >>> d2.seconds
    28800
    """

    def __init__(self, utc):
        utc = str(utc.strip().upper())
        mt = _RE_TZ.match(utc)
        if mt:
            minus = mt.group(1) == '-'
            h = int(mt.group(2))
            m = int(mt.group(3))
            if minus:
                h, m = (-h), (-m)
            self._utcoffset = datetime.timedelta(hours=h, minutes=m)
            self._tzname = 'UTC%s' % utc
        else:
            raise ValueError('bad utc time zone')

    def utcoffset(self, dt):
        return self._utcoffset

    def dst(self, dt):
        return _TIMEDELTA_ZERO

    def tzname(self, dt):
        return self._tzname

    def __str__(self):
        return 'UTC tzinfo object (%s)' % self._tzname

    __repr__ = __str__


# 常用时区
UTC_0, UTC_8 = UTC('+00:00'), UTC('+08:00')
# 常用日期时间定义
LOCAL_DATE_TIME_PATTERN = '%Y-%m-%dT%H:%M:%S'
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


def utc_8_now(ret="str", is_date=False):
    if ret == "date" or is_date:
        now = datetime.datetime.utcnow().replace(tzinfo=UTC_0).astimezone(UTC_8).date()
    elif ret == "datetime":
        now = datetime.datetime.utcnow().replace(tzinfo=UTC_0).astimezone(UTC_8)
    else:
        now = datetime.datetime.utcnow().replace(tzinfo=UTC_0).astimezone(UTC_8).strftime(DATETIME_FORMAT)
    return now


def utc_8_day():
    day = datetime.datetime.utcnow().replace(tzinfo=UTC_0).astimezone(UTC_8).strftime(DATE_FORMAT)
    return day


def utc_now():
    now = datetime.datetime.utcnow().replace(tzinfo=UTC_0).strftime(DATETIME_FORMAT)
    return now


def utc_to_local(dt, is_date=False, ret="str"):
    if isinstance(dt, str):
        if is_date:
            dt = datetime.datetime.strptime(dt, DATE_FORMAT).replace(tzinfo=UTC_0).astimezone(UTC_8)
        else:
            dt = datetime.datetime.strptime(dt, LOCAL_DATE_TIME_PATTERN).replace(tzinfo=UTC_0).astimezone(UTC_8)
    elif isinstance(dt, datetime.datetime):
        dt = dt.replace(tzinfo=UTC_0).astimezone(UTC_8)
    else:
        raise ValueError("Param[%s] should be a valid datetime or str of datetime." % dt)
    dt = dt.replace(tzinfo=None)
    dt_str = dt.strftime(DATE_FORMAT) if is_date else dt.strftime(LOCAL_DATE_TIME_PATTERN)
    return dt if ret == "datetime" else dt.date() if ret == "date" else dt_str


def utc_to_utc_8(dt, is_date=False, ret="str"):
    if isinstance(dt, str):
        if is_date:
            dt = datetime.datetime.strptime(dt, DATE_FORMAT).replace(tzinfo=UTC_0).astimezone(UTC_8)
        else:
            dt = datetime.datetime.strptime(dt, DATETIME_FORMAT).replace(tzinfo=UTC_0).astimezone(UTC_8)
    elif isinstance(dt, datetime.datetime):
        dt = dt.replace(tzinfo=UTC_0).astimezone(UTC_8)
    else:
        raise ValueError("Param[%s] should be a valid datetime or str of datetime." % dt)
    dt = dt.replace(tzinfo=None)
    dt_str = dt.strftime(DATE_FORMAT) if is_date else dt.strftime(DATETIME_FORMAT)
    return dt if ret == "datetime" else dt.date() if ret == "date" else dt_str


def utc_8_to_utc(dt, is_date=False, ret="str"):
    if isinstance(dt, unicode):
        dt = dt.encode('utf-8')
    if isinstance(dt, str):
        if is_date:
            dt = datetime.datetime.strptime(dt, DATE_FORMAT).replace(tzinfo=UTC_8).astimezone(UTC_0)
        else:
            dt = datetime.datetime.strptime(dt, DATETIME_FORMAT).replace(tzinfo=UTC_8).astimezone(UTC_0)
    elif isinstance(dt, datetime.datetime):
        dt = dt.replace(tzinfo=UTC_8).astimezone(UTC_0)
    else:
        raise ValueError("Param[%s] should be a valid datetime or str of datetime." % dt)
    dt = dt.replace(tzinfo=None)
    dt_str = dt.strftime(DATE_FORMAT) if is_date else dt.strftime(DATETIME_FORMAT)
    return dt if ret == "datetime" else dt.date() if ret == "date" else dt_str


def n_days_before(n, ret="str"):
    n = int(n)
    now = datetime.datetime.utcnow().replace(tzinfo=UTC_0).astimezone(UTC_8)
    days = datetime.timedelta(days=n)
    n_day_before = now - days
    dt_str = n_day_before.strftime(DATETIME_FORMAT)
    return n_day_before if ret == "datetime" else n_day_before.date() if ret == "date" else dt_str


def check_interval(date_str, days):
    past_date = datetime.datetime.strptime(date_str, DATE_FORMAT).date()
    days = int(days)
    from_date = datetime.date.fromordinal(datetime.date.today().toordinal() - days)
    now = datetime.datetime.utcnow().replace(tzinfo=UTC_0).astimezone(UTC_8).date()
    if from_date <= past_date <= now:
        return True
    else:
        return False


def last_month():
    last_day = (
        datetime.datetime.utcnow().replace(tzinfo=UTC_0).astimezone(UTC_8).replace(day=1) - datetime.timedelta(days=1))
    first_day = last_day.replace(day=1)
    # 上个月的天数, 上个月的第一天, 上个月的最后一天
    return (last_day - first_day).days + 1, first_day.strftime(DATE_FORMAT), last_day.strftime(DATE_FORMAT)


def day_range(year=0, month=0, day=0, value=None, tz=UTC_8):
    # 传入的日期是本地时区
    pass


def month_range(year, month, value=None, tz=UTC_8):
    # 传入的日期是本地时区
    pass
