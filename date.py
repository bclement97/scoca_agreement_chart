from calendar import timegm
from datetime import datetime, time, timedelta
from time import gmtime, localtime, mktime


DEFAULT_START_DATE = '2019-01-03'  # This is the start of the newest Assoc. Justice's tenure (J. Groban).
DATE_FORMAT = '%Y-%m-%d'
MON, TUE, WED, THU, FRI, SAT, SUN = range(7)


def date_to_str(date):
    return date.strftime(DATE_FORMAT)


def local_to_utc(dt):
    t = localtime()
    seconds_delta = timegm(t) - timegm(gmtime(mktime(t)))
    return dt - timedelta(seconds=seconds_delta)


def next_posting_date(ref_date=datetime.now()):
    """Returns the next posting date for published SCOCA opinions (Monday/Thursday, 10am) after REF_DATE.
    """

    def date_at_10am(date):
        """Returns DATE at 10am.
        """
        time_10am = time(10)
        return datetime.combine(date, time_10am)

    def next_day(day):
        """Returns the date of the next occurrence of DAY (monday=0 ... sunday=6) or the current date if DAY is today.
        """
        days_delta = (day - ref_date.weekday()) % 7
        dt_next_day = ref_date + timedelta(days=days_delta)
        return dt_next_day.date()

    next_monday_10am = date_at_10am(next_day(MON))
    next_thursday_10am = date_at_10am(next_day(THU))

    timedelta_monday_10am = next_monday_10am - ref_date
    timedelta_thursday_10am = next_thursday_10am - ref_date

    no_timedelta = timedelta()

    # If one datetime is at or before now, select the other datetime
    if timedelta_monday_10am <= no_timedelta:
        return next_thursday_10am
    elif timedelta_thursday_10am <= no_timedelta:
        return next_monday_10am
    # Otherwise, choose the closest one
    elif timedelta_monday_10am < timedelta_thursday_10am:
        return next_monday_10am
    else:
        return next_thursday_10am
