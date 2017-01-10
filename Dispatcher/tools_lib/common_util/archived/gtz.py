# coding:utf-8
# 统一的时区处理类
import pytz
import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse


class TimeZone(object):
    UTC_TIMEZONE = pytz.utc
    DEFAULT_TIMEZONE = pytz.timezone('Asia/Shanghai')
    UTC_DATE_TIME_PATTERN = '%Y-%m-%dT%H:%M:%SZ'
    DATE_PATTERN = "%Y-%m-%d"
    DATE_PATTERN_WITH_NO_YEAR = "%m-%d"
    TIME_PATTERN = "%H:%M"
    SQL_DATETIME_PATTERN = '%Y-%m-%d %H:%M:%S'
    DATE_TIME_PATTERN = "%m-%d %H:%M"

    @classmethod
    def is_naive(cls, value):
        """
        Determines if a given datetime.datetime is naive.
        @param value:
        @return:
        """
        return value.tzinfo is None or value.tzinfo.utcoffset(value) is None

    @classmethod
    def is_aware(cls, value):
        """
        Determines if a given datetime.datetime is aware.
        @param value:
        @return:
        """
        return value.tzinfo is not None and value.tzinfo.utcoffset(value) is not None

    @classmethod
    def localtime(cls, d, tz=None):
        """
        Converts an aware datetime.datetime to local time.
        Local time is defined by the default time zone, unless another time zone is specified.
        @param d:
        @param tz:
        @return:
        """
        if tz is None:
            tz = cls.DEFAULT_TIMEZONE
        value = d.astimezone(tz)
        if hasattr(tz, 'normalize'):
            # 对于采用了夏时制的时区需要使用normalize方法进行处理
            value = tz.normalize(value)
        return value

    @classmethod
    def naive_to_aware(cls, naive_datetime, tz=None):
        """
        非时区datetime对象转换为带时区属性的datetime对象
        @param naive_datetime:
        @param tz:
        @return:
        """
        if tz is None:
            tz = cls.DEFAULT_TIMEZONE
        return tz.localize(naive_datetime)

    @classmethod
    def datetime_to_timezone(cls, d, tz=pytz.utc):
        """
        把datetime类型的日期转换为tz时区，如果原来是非时区日期则直接转化为tz时区
        @param d:
        @param tz:
        @return:
        """
        if cls.is_naive(d):
            return cls.naive_to_aware(d, tz=tz)
        return cls.localtime(d, tz=tz)

    @classmethod
    def datetime_to_utc(cls, d):
        return cls.datetime_to_timezone(d, tz=pytz.utc)

    @classmethod
    def utc_to_local(cls, d):
        """
        把utc时间转换为本地时间, 如果输入的datetime不含有tzinfo, 则自定加上
        """
        if cls.is_naive(d):
            d = cls.naive_to_aware(d, tz=pytz.utc)
        return cls.localtime(d)

    @classmethod
    def utc_now(cls):
        return cls.naive_to_aware(datetime.datetime.utcnow(), tz=pytz.utc)

    @classmethod
    def local_now(cls):
        return cls.naive_to_aware(datetime.datetime.now(), tz=cls.DEFAULT_TIMEZONE)

    @classmethod
    def increment_years(cls, d, n=1):
        assert n >= 0
        return d + relativedelta(years=n)

    @classmethod
    def decrement_years(cls, d, n=1):
        assert n >= 0
        return d - relativedelta(years=n)

    @classmethod
    def increment_months(cls, d, n=1):
        assert n >= 0
        return d + relativedelta(months=n)

    @classmethod
    def decrement_months(cls, d, n=1):
        assert n >= 0
        return d - relativedelta(months=n)

    @classmethod
    def increment_days(cls, d, n=1):
        assert n >= 0
        return d + relativedelta(days=n)

    @classmethod
    def decrement_days(cls, d, n=1):
        assert n >= 0
        return d - relativedelta(days=n)

    @classmethod
    def increment_seconds(cls, d, n=1):
        assert n >= 0
        return d + relativedelta(seconds=n)

    @classmethod
    def decrement_seconds(cls, d, n=1):
        assert n >= 0
        return d - relativedelta(seconds=n)

    @classmethod
    def increment_hours(cls, d, n=1):
        assert n >= 0
        return d + relativedelta(hours=n)

    @classmethod
    def decrement_hours(cls, d, n=1):
        assert n >= 0
        return d - relativedelta(hours=n)

    @classmethod
    def increment_minutes(cls, d, n=1):
        assert n >= 0
        return d + relativedelta(minutes=n)

    @classmethod
    def decrement_minutes(cls, d, n=1):
        assert n >= 0
        return d - relativedelta(minutes=n)

    @classmethod
    def year_range(cls, year, value=None, tz=pytz.utc):
        # 传入的日期是本地时区
        if value:
            year = value.year
        assert year >= 0
        start_date = cls.naive_to_aware(datetime.datetime(year, 1, 1), tz=cls.DEFAULT_TIMEZONE)
        end_date = cls.increment_years(start_date)
        return cls.datetime_to_timezone(start_date, tz), cls.datetime_to_timezone(end_date, tz)

    @classmethod
    def month_range(cls, year=0, month=0, value=None, tz=pytz.utc):
        # 传入的日期是本地时区
        if value:
            year, month = value.year, value.month
        assert year >= 0
        assert 12 >= month >= 1
        start_date = cls.naive_to_aware(datetime.datetime(year, month, 1), tz=cls.DEFAULT_TIMEZONE)
        end_date = cls.increment_months(start_date)
        return cls.datetime_to_timezone(start_date, tz), cls.datetime_to_timezone(end_date, tz)

    @classmethod
    def day_range(cls, year=0, month=0, day=0, value=None, tz=pytz.utc):
        # 传入的日期是本地时区
        if value:
            year, month, day = value.year, value.month, value.day
        assert year >= 0
        assert 12 >= month >= 1
        assert 31 >= day >= 1
        start_datetime = cls.naive_to_aware(datetime.datetime(year, month, day), tz=cls.DEFAULT_TIMEZONE)
        end_datetime = cls.increment_days(start_datetime)
        return cls.datetime_to_timezone(start_datetime, tz), cls.datetime_to_timezone(end_datetime, tz)

    @classmethod
    def date_xrange(cls, start_date, end_date, step=1):
        day = start_date
        while True:
            if day < end_date:
                yield day
                day = cls.increment_days(day, step)
            else:
                break

    @classmethod
    def datetime_to_str(cls, d, pattern=None):
        if pattern is None:
            pattern = cls.UTC_DATE_TIME_PATTERN
        return d.strftime(pattern)

    @classmethod
    def str_to_datetime(cls, d_str):
        d = parse(d_str)
        if d.tzinfo != pytz.utc:
            d = cls.datetime_to_utc(d)
        return d

    @classmethod
    def date_to_str(cls, d, pattern=None):
        if pattern is None:
            pattern = cls.DATE_PATTERN
        return d.strftime(pattern)

    @classmethod
    def str_to_date(cls, d_str):
        return parse(d_str).date()

    @classmethod
    def time_to_str(cls, t):
        return t.strftime(cls.TIME_PATTERN)

    @classmethod
    def transfer_datetime_to_beginning(cls, d):
        """
        返回传入日期的当天起始时间
        @param d:
        @return:
        """
        return d.replace(hour=0, minute=0, second=0, microsecond=0)

    @classmethod
    def date_to_datetime(cls, d, tz=None):
        """
        date 转 datetime
        @param d:
        @param tz:
        @return:
        """
        value = datetime.datetime(d.year, d.month, d.day)
        if tz is not None:
            value = cls.naive_to_aware(value, tz=tz)
        return value

    @classmethod
    def format_to_sql_datetime(cls, d):
        return d.strftime(cls.SQL_DATETIME_PATTERN)


if __name__ == '__main__':
    local_now = datetime.datetime.now()
    print('local_time: %s' % TimeZone.naive_to_aware(local_now, pytz.timezone(pytz.country_timezones('cn')[0])))
    print('local_time: %s' % TimeZone.naive_to_aware(local_now))
    print('utc_time: %s' % TimeZone.datetime_to_utc(local_now))
    print('utc_time_str: %s' % TimeZone.datetime_to_str(TimeZone.datetime_to_utc(local_now)))
    print('date str: %s' % TimeZone.str_to_date('2015-12-06'))
    print('utc_now: %s' % TimeZone.utc_now())
    print('local_now: %s' % TimeZone.local_now())

    print('first in 2014-08 in utc: %s' % TimeZone.datetime_to_utc(
        TimeZone.naive_to_aware(datetime.datetime(2014, 8, 1))))
    print('first in 2014-08 in utc: %s' % TimeZone.datetime_to_utc(
        TimeZone.naive_to_aware(datetime.datetime(2014, 9, 1))))

    local_d1 = datetime.datetime(2014, 9, 15, 23, 22, 10)
    assert TimeZone.naive_to_aware(local_d1, tz=pytz.utc) == TimeZone.utc_to_local(TimeZone.datetime_to_utc(local_d1))

    print('2013-12: (%s~%s)' % (TimeZone.month_range(2013, 12)))
    print('2014-01: (%s~%s)' % (TimeZone.month_range(2014, 1)))

    print('2014-01-01: (%s~%s)' % (TimeZone.day_range(2014, 1, 1)))
    print('2013-12-31: (%s~%s)' % (TimeZone.day_range(2013, 12, 31)))
    print('2012-03-01: (%s~%s)' % (TimeZone.day_range(2012, 3, 1)))
    print('2014-03-01: (%s~%s)' % (TimeZone.day_range(2014, 3, 1)))
