import logging

import atom
import gdata.alt.appengine
import gdata.calendar
import gdata.calendar.service

from util import tz

_GDATA_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'

def _login():
  client = gdata.calendar.service.CalendarService()
  gdata.alt.appengine.run_on_appengine(client, store_tokens=False, 
      single_user_mode=True)

  client.email = 'aacosf@aaco-sf.org'
  client.password = 'handson'
  client.source = 'aaco-events-1.0'
  client.ProgrammaticLogin()

  return client

def _fill_gdata_event(gd_event, event_vo, event_preview_text):
  
  gd_event.title = atom.Title(text=event_vo.title)
  content = "%s\n\n\nkey: %s" % (event_preview_text, event_vo.key)
  gd_event.content = atom.Content(text=content)
  gd_event.where.append(gdata.calendar.Where(value_string=event_vo.location))

  for time_vo in event_vo.times:
    start = time_vo.start.astimezone(tz.utc).strftime(_GDATA_TIME_FORMAT)
    end = time_vo.end.astimezone(tz.utc).strftime(_GDATA_TIME_FORMAT)

    gd_event.when.append(gdata.calendar.When(start_time=start, end_time=end))

  return gd_event

def add_event(event_vo, event_preview_text):
#  if event_vo.flag_is_draft:
#    return

  client = _login()

  gd_event = _fill_gdata_event(gdata.calendar.CalendarEventEntry(), event_vo,
      event_preview_text)
  new_event = client.InsertEvent(gd_event,
      '/calendar/feeds/default/private/full')

  return new_event

def update_events(events):
  client = _login()

  logging.info("gcal: events: %s", events)
  for event_vo, event_preview in events:
    # search for it
    query = gdata.calendar.service.CalendarEventQuery('default', 'private',
         'full', str(event_vo.key))
    feed = client.CalendarQuery(query)

    # delete old ones
    for gd_event in feed.entry:
      client.DeleteEvent(gd_event.GetEditLink().href)

    logging.info("gcal: adding %s", event_vo)
    gd_event = _fill_gdata_event(gdata.calendar.CalendarEventEntry(), event_vo,
       event_preview)
    new_event = client.InsertEvent(gd_event,
       '/calendar/feeds/default/private/full')
