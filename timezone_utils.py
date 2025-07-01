"""
Timezone utilities for handling PST/PDT timezone conversions
Uses pytz for reliable timezone handling in production environments
"""
from datetime import datetime
import pytz

# US/Pacific timezone automatically handles PST/PDT transitions
PACIFIC_TZ = pytz.timezone('US/Pacific')

def get_pacific_timezone():
    """
    Get the US/Pacific timezone which automatically handles PST/PDT.
    """
    return PACIFIC_TZ

def now_pst():
    """
    Get the current datetime in Pacific timezone (PST/PDT).
    """
    return datetime.now(PACIFIC_TZ)

def utc_to_pst(utc_dt):
    """
    Convert UTC datetime to Pacific timezone (PST/PDT).
    """
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
    return utc_dt.astimezone(PACIFIC_TZ)

def pst_to_utc(pst_dt):
    """
    Convert Pacific timezone datetime to UTC.
    """
    if pst_dt.tzinfo is None:
        pst_dt = PACIFIC_TZ.localize(pst_dt)
    return pst_dt.astimezone(pytz.utc)

def format_pst_date(dt=None, format_str="%Y-%m-%d"):
    """
    Format a datetime in Pacific timezone.
    If no datetime is provided, uses current Pacific time.
    """
    if dt is None:
        dt = now_pst()
    elif dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = pytz.utc.localize(dt).astimezone(PACIFIC_TZ)
    elif dt.tzinfo != PACIFIC_TZ:
        dt = dt.astimezone(PACIFIC_TZ)
    return dt.strftime(format_str)

def format_pst_time(dt=None, format_str="%H:%M:%S"):
    """
    Format a time in Pacific timezone.
    If no datetime is provided, uses current Pacific time.
    """
    if dt is None:
        dt = now_pst()
    elif dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = pytz.utc.localize(dt).astimezone(PACIFIC_TZ)
    elif dt.tzinfo != PACIFIC_TZ:
        dt = dt.astimezone(PACIFIC_TZ)
    return dt.strftime(format_str)

def format_pst_datetime(dt=None, format_str="%A, %B %d, %Y"):
    """
    Format a full datetime string in Pacific timezone.
    If no datetime is provided, uses current Pacific time.
    """
    if dt is None:
        dt = now_pst()
    elif dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = pytz.utc.localize(dt).astimezone(PACIFIC_TZ)
    elif dt.tzinfo != PACIFIC_TZ:
        dt = dt.astimezone(PACIFIC_TZ)
    return dt.strftime(format_str)

def get_pst_weekday(dt=None):
    """
    Get the weekday abbreviation in Pacific timezone.
    If no datetime is provided, uses current Pacific time.
    """
    if dt is None:
        dt = now_pst()
    elif dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = pytz.utc.localize(dt).astimezone(PACIFIC_TZ)
    elif dt.tzinfo != PACIFIC_TZ:
        dt = dt.astimezone(PACIFIC_TZ)
    return dt.strftime("%a")

def is_before_noon_pst(time_str):
    """
    Check if a time string (HH:MM:SS format) represents a time before noon in PST.
    """
    try:
        time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
        return time_obj.hour < 12
    except ValueError:
        return False
