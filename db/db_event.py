import datetime
import itertools
import logging

from google.appengine.ext import db

from util import tz

#
# Data Models
#

class Event(db.Expando):

  starts = db.ListProperty(datetime.datetime)
  ends = db.ListProperty(datetime.datetime)

  type = db.IntegerProperty(required=True)
  title = db.StringProperty(required=True)
  description = db.TextProperty(required=True)
  location = db.TextProperty(required=False)
  contact = db.TextProperty(required=False)

  flag_is_active = db.BooleanProperty(default=True)
  flag_is_full = db.BooleanProperty(default=False)
  flag_is_draft = db.BooleanProperty(default=True)
  flag_is_published = db.BooleanProperty(default=False)

  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)

  creator = db.UserProperty()

# rsvp = db.Reference(Contact, required=True)

#
# Value Objects
#

ONE_DAY_DELTA = datetime.timedelta(1)
class TimeVO(object):
  def __init__(self, start, end):
    if not start.tzinfo:
      self.start = start.replace(tzinfo=tz.utc).astimezone(tz.us_pacific)
    else:
      self.start = start

    if not end.tzinfo:
      self.end = end.replace(tzinfo=tz.utc).astimezone(tz.us_pacific)
    else:
      self.end = end

    if (end - start) <= ONE_DAY_DELTA:
      self.is_same_day = True
    else:
      self.is_same_day = False

  def __repr__(self):
    return str({
      'start': self.start,
      'end': self.end,
    })


EVENT_TYPE_VOLUNTEER = 1
EVENT_TYPE_COMMUNITY = 2

EVENT_TYPES = [
    (EVENT_TYPE_VOLUNTEER, "Volunteer"),
    (EVENT_TYPE_COMMUNITY, "Community"),
]

EVENT_TYPES_DICT = dict(EVENT_TYPES)

class EventVO(object):
  def __init__(self, model):
    self.times = sorted(
        [TimeVO(s, e) for s,e in itertools.izip(model.starts, model.ends)],
        reverse=True)
    for name, value in model.properties().iteritems():
      setattr(self, name, getattr(model, name))

    self.type_text = EVENT_TYPES_DICT[model.type]

    self.key = model.key()

  def __repr__(self):
    return str({
      'times': self.times,
      'type': self.type,
      'title': self.title,
      'description': self.description,
      'location': self.location,
      'contact': self.contact,
      'is_full': self.flag_is_full,
      'is_draft': self.flag_is_draft,
      'created': self.created,
      'updated': self.updated,
      'key': self.key,
    })


#
# helper functions
#

def _filter_event_dates(event):
  cutoff_dt = datetime.datetime.now(tz.us_pacific)
  event.times = filter(lambda d: d.start > cutoff_dt and d.end > cutoff_dt,
      event.times)

  return event

#
#
#

def update_event(**kwargs):
  event = db.get(kwargs['key'])

  for key,value in itertools.ifilter(lambda k: k[0] != 'key', kwargs.iteritems()):
    setattr(event, key, value)

  db.put(event)

  return EventVO(event)

def add_event(**kwargs):
  event = Event(**kwargs)
  db.put(event)

  return EventVO(event)

def get_event(key):
  return EventVO(db.get(key))

def get_events(keys):
  return itertools.imap(lambda x: get_event(x), keys)

def get_publishable_events(keys):
  return filter(lambda e: not e.flag_is_draft,
      itertools.imap(_filter_event_dates,
        itertools.imap(lambda x: get_event(x), keys)))

def get_published_events():
  events = itertools.imap(lambda e: EventVO(e),
      Event.all().filter('flag_is_published =', True))
  return filter(lambda e: not e.flag_is_draft,
      itertools.imap(_filter_event_dates, events))

def get_active_events_by_end_date(end, delta=None):
  raw_events = db.Query(Event).filter('ends >', end)

  current_active = itertools.ifilter(lambda e: e.flag_is_active, raw_events)
  if delta:
    current_active = itertools.ifilter(
        lambda e: filter(lambda x: x <= end+delta, e.starts), current_active)

  return itertools.imap(lambda x: EventVO(x), current_active)

def set_multiple_published(keys):
  for key in keys:
    event = db.get(key)
    event.flag_is_published = True
    db.put(event)

def clear_all_published():
  events = Event.all().filter('flag_is_published =', True)
  for event in events:
    event.flag_is_published = False
    db.put(event)

def delete_event(encoded_key):
  event = db.get(encoded_key)
  event.flag_is_active = False

  db.put(event)
