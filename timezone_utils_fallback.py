"""
Alternative timezone utilities that work without pytz dependency
Uses built-in datetime with manual DST calculation
"""
from datetime import datetime, timezone, timedelta

# PST is UTC-8, PDT is UTC-7
PST = timezone(timedelta(hours=-8))
PDT = timezone(timedelta(hours=-7))

def get_pst_timezone():
    """
    Get the appropriate PST/PDT timezone based on daylight saving time.
    Returns PST (UTC-8) or PDT (UTC-7) depending on the current date.
    """
    # Simple daylight saving time check for US Pacific timezone
    # DST typically runs from second Sunday in March to first Sunday in November
    now_utc = datetime.now(timezone.utc)
    year = now_utc.year
    
    # Calculate DST start (second Sunday in March)
    march_first = datetime(year, 3, 1, tzinfo=timezone.utc)
    days_to_sunday = (6 - march_first.weekday()) % 7
    first_sunday_march = march_first + timedelta(days=days_to_sunday)
    dst_start = first_sunday_march + timedelta(days=7)  # Second Sunday
    dst_start = dst_start.replace(hour=10)  # 2 AM PST = 10 AM UTC
    
    # Calculate DST end (first Sunday in November)
    november_first = datetime(year, 11, 1, tzinfo=timezone.utc)
    days_to_sunday = (6 - november_first.weekday()) % 7
    dst_end = november_first + timedelta(days=days_to_sunday)
    dst_end = dst_end.replace(hour=9)  # 2 AM PDT = 9 AM UTC
    
    # Check if we're in daylight saving time
    if dst_start <= now_utc < dst_end:
        return PDT  # Daylight saving time (UTC-7)
    else:
        return PST  # Standard time (UTC-8)

def now_pst():
    """
    Get the current datetime in PST/PDT timezone.
    """
    return datetime.now(get_pst_timezone())

def utc_to_pst(utc_dt):
    """
    Convert UTC datetime to PST/PDT.
    """
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(get_pst_timezone())

def pst_to_utc(pst_dt):
    """
    Convert PST/PDT datetime to UTC.
    """
    if pst_dt.tzinfo is None:
        pst_dt = pst_dt.replace(tzinfo=get_pst_timezone())
    return pst_dt.astimezone(timezone.utc)

def format_pst_date(dt=None, format_str="%Y-%m-%d"):
    """
    Format a datetime in PST timezone.
    If no datetime is provided, uses current PST time.
    """
    if dt is None:
        dt = now_pst()
    elif dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=timezone.utc).astimezone(get_pst_timezone())
    return dt.strftime(format_str)

def format_pst_time(dt=None, format_str="%H:%M:%S"):
    """
    Format a time in PST timezone.
    If no datetime is provided, uses current PST time.
    """
    if dt is None:
        dt = now_pst()
    elif dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=timezone.utc).astimezone(get_pst_timezone())
    return dt.strftime(format_str)

def format_pst_datetime(dt=None, format_str="%A, %B %d, %Y"):
    """
    Format a full datetime string in PST timezone.
    If no datetime is provided, uses current PST time.
    """
    if dt is None:
        dt = now_pst()
    elif dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=timezone.utc).astimezone(get_pst_timezone())
    return dt.strftime(format_str)

def get_pst_weekday(dt=None):
    """
    Get the weekday abbreviation in PST timezone.
    If no datetime is provided, uses current PST time.
    """
    if dt is None:
        dt = now_pst()
    elif dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=timezone.utc).astimezone(get_pst_timezone())
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
