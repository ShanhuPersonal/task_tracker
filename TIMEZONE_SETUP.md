# Timezone Configuration for EC2 Deployment

## Overview
This Flask application has been configured to handle Pacific Standard Time (PST) and Pacific Daylight Time (PDT) when deployed on AWS EC2 instances that run in UTC.

## Changes Made

### 1. Created `timezone_utils.py`
- Handles PST/PDT timezone conversions
- Uses `pytz` library for reliable timezone handling (with fallback)
- Automatically handles daylight saving time transitions

### 2. Updated Application Files
- `routes/tasks.py` - All datetime operations now use PST
- `routes/history.py` - Historical data displayed in PST
- `routes/ai_problems.py` - AI problem generation uses PST dates  
- `openai_helper.py` - Question logging uses PST timestamps

### 3. Updated `requirements.txt`
- Added `pytz==2023.3` for reliable timezone support

## Installation on EC2

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Verify Timezone Support
```python
from timezone_utils import now_pst, format_pst_datetime
print(f"Current PST time: {format_pst_datetime()}")
```

### 3. Optional: Set System Timezone (for logging consistency)
```bash
# Set system timezone to Pacific (optional)
sudo timedatectl set-timezone America/Los_Angeles

# Verify
timedatectl
```

## How It Works

### Without pytz (fallback mode)
- Uses manual DST calculation
- Handles PST (UTC-8) and PDT (UTC-7) automatically
- Calculates DST transitions based on US rules

### With pytz (recommended for production)
- Uses `pytz.timezone('US/Pacific')`
- Automatically handles all timezone complexities
- More reliable for edge cases

## Functions Available

### Core Functions
- `now_pst()` - Get current time in PST/PDT
- `format_pst_date()` - Format date in PST
- `format_pst_time()` - Format time in PST
- `format_pst_datetime()` - Format full datetime in PST
- `get_pst_weekday()` - Get weekday in PST

### Conversion Functions
- `utc_to_pst(utc_dt)` - Convert UTC to PST
- `pst_to_utc(pst_dt)` - Convert PST to UTC

## Testing

### Local Testing
```python
from timezone_utils import now_pst, utc_to_pst
from datetime import datetime, timezone

# Test current PST time
print(f"PST Now: {now_pst()}")

# Test UTC conversion
utc_time = datetime.now(timezone.utc)
pst_time = utc_to_pst(utc_time)
print(f"UTC: {utc_time}")
print(f"PST: {pst_time}")
```

### On EC2
```bash
# Check system time (should be UTC)
date

# Check application time
python3 -c "from timezone_utils import now_pst; print(f'App PST time: {now_pst()}')"
```

## Deployment Checklist

1. ✅ Install `pytz` package
2. ✅ Update all datetime usage to use timezone_utils
3. ✅ Test timezone conversions
4. ✅ Verify task scheduling works in PST
5. ✅ Check AI problem generation uses PST dates
6. ✅ Confirm history displays in PST

## Important Notes

- The application will automatically detect if `pytz` is available
- If `pytz` is not installed, it falls back to manual DST calculation
- All user-facing times will be displayed in PST/PDT
- Database stores dates as strings in PST format
- Log files will show PST timestamps

## Troubleshooting

### If times seem incorrect:
1. Check if `pytz` is installed: `pip show pytz`
2. Verify system UTC time: `date -u`
3. Test timezone functions manually
4. Check for any remaining `datetime.now()` calls in code

### For debugging:
```python
from timezone_utils import now_pst, get_pacific_timezone
print(f"Current timezone: {get_pacific_timezone()}")
print(f"Current PST time: {now_pst()}")
```
