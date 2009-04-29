__author__ = 'Herbert Ho'

import datetime
import string
import time

from google.appengine.ext.webapp import template

from util import tz


_DATE_FORMAT = "%m/%d/%Y"
def input_date(timestamp):
  if not timestamp: return ''
  return timestamp.astimezone(tz.us_pacific).strftime(_DATE_FORMAT)

_TIME_FORMAT = "%I:%M %p"
def input_time(timestamp):
  if not timestamp: return ''
  return timestamp.astimezone(tz.us_pacific).strftime(_TIME_FORMAT)

_PRETTY_DATETIME_FORMAT = "%A, %B %d, %Y, %I:%M %p"
def pretty_datetime(timestamp):
  if not timestamp: return ''
  return timestamp.astimezone(tz.us_pacific).strftime(_PRETTY_DATETIME_FORMAT)

_PRETTY_DATE_FORMAT = "%A, %B %d, %Y"
def pretty_date(timestamp):
  if not timestamp: return ''
  return timestamp.astimezone(tz.us_pacific).strftime(_PRETTY_DATE_FORMAT)

_PRETTY_TIME_FORMAT = "%I:%M %p"
def pretty_time(timestamp):
  if not timestamp: return ''
  return timestamp.astimezone(tz.us_pacific).strftime(_PRETTY_TIME_FORMAT)

def rfc3339date(date):
  """Formats the given date in RFC 3339 format for feeds."""
  if not date: return ''
  date = date + datetime.timedelta(seconds=-time.timezone)
  if time.daylight:
    date += datetime.timedelta(seconds=time.altzone)
  return date.strftime('%Y-%m-%dT%H:%M:%SZ')

def indenttext(lines, indent_count, ignore_first=True):
  if not lines: return ''

  indent_str = "\t".expandtabs(indent_count)

  first = True
  result = []
  for line in lines.splitlines():
    if first and ignore_first:
      result.append(line)
      first = False
      continue
    result.append("%s%s" % (indent_str, line))

  return "\n".join(result)

def postpadding(to_pad, amount, space=True, character='-'):
  pad_amt = amount - len(to_pad)
  if space:
    pad_amt = pad_amt - 1

  pad_amt = max(0, pad_amt)

  trailing = character.join(['' for x in range(-1, pad_amt)])
  if space:
    return to_pad + " " + trailing
  else:
    return to_pad + trailing


# Register the filter functions with Django
register = template.create_template_register()
register.filter(rfc3339date)
register.filter(input_date)
register.filter(input_time)
register.filter(pretty_datetime)
register.filter(pretty_date)
register.filter(pretty_time)
register.filter(indenttext)
register.filter(postpadding)
