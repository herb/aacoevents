#!/usr/bin/env python

__author__ = 'Herbert Ho'

import datetime
import itertools
import logging
import random
import string
import sys
import time
import wsgiref.handlers

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required

from db import db_event
from db import db_log
from servlets import base
from util import gcal
from util import tz


# Add our custom Django template filters to the built in filters
template.register_template_library('filters')


#
# helper functions
#

DATETIME_FORMAT = "%m/%d/%Y %I:%M %p"
def _parse_datetimes(request, prefix):
  _make_dt = lambda (x,y): datetime.datetime(tzinfo=tz.us_pacific,
      *time.strptime("%s %s" % (x,y), DATETIME_FORMAT)[0:6])

  aggr_itr = itertools.izip(request.get_all(prefix+'date'),
      request.get_all(prefix+'time'))
  return map(_make_dt, aggr_itr)


#
# pages
#


class EventIndexPage(base.BaseRequestHandler):
  def get(self):
    self.generate("events/index.tmpl", {})

  def post(self):
    self.generate("events/index.tmpl", {})

ONE_MONTH_DELTA = datetime.timedelta(31)
TWO_MONTH_DELTA = datetime.timedelta(61)
class EventListPage(base.BaseRequestHandler):
  def _list(self):
    events = db_event.get_active_events_by_end_date(datetime.datetime.today())

    self.generate('events/event_list.tmpl', {
      'events': events,
      'debug_info': str(events),
    })

  def get(self):
    self._list()

  def post(self):
    if self.request.get('delete'):
      maker = db_event.get_event(self.request.get('delete')).creator
      if maker != users.get_current_user() and not users.is_current_user_admin():
        self.errors.append("operation not permitted")
      else:
        db_event.delete_event(self.request.get('delete'))
        db_log.log_action(db_log.ACTION_DELETE, users.get_current_user(),
            self.request.get('delete'))

    self._list()

class EventAddPage(base.BaseRequestHandler):

  def get(self):
    self.generate('events/event_add.tmpl', {'EVENT_TYPES': db_event.EVENT_TYPES})

  def post(self):
    values = {
        'starts': _parse_datetimes(self.request, prefix='begin_'),
        'ends': _parse_datetimes(self.request, prefix='end_'),

        'type': int(self.request.get('type')),
        'flag_is_full': bool(self.request.get('is_full')),
        'flag_is_draft': bool(self.request.get('is_draft')),
        'title': self.request.get('title'),
        'description': self.request.get('description'),
        'contact': self.request.get('contact'),
        'location': self.request.get('location'),
    }

    event = db_event.add_event(creator=users.get_current_user(), **values)
    db_log.log_action(db_log.ACTION_CREATE, users.get_current_user(),
        str(event.key))

    self.display['event'] = event
    self.display['EVENT_TYPES'] = db_event.EVENT_TYPES

    self.messages.append("added")

    self.generate('events/event_add.tmpl', values)

class EventEditPage(base.BaseRequestHandler):
  def get(self):
    event = db_event.get_event(self.request.get('key'))
    self.display['event'] = event
    self.display['EVENT_TYPES'] = db_event.EVENT_TYPES

    self.generate('events/event_add.tmpl')

  def post(self):
    key = self.request.get('edit')
    if key:
      values = {
          'starts': _parse_datetimes(self.request, prefix='begin_'),
          'ends': _parse_datetimes(self.request, prefix='end_'),

          'type': int(self.request.get('type')),
          'flag_is_full': bool(self.request.get('is_full')),
          'flag_is_draft': bool(self.request.get('is_draft')),
          'title': self.request.get('title'),
          'description': self.request.get('description'),
          'contact': self.request.get('contact'),
          'location': self.request.get('location'),
      }

      event = db_event.update_event(key=key, **values)
      db_log.log_action(db_log.ACTION_UPDATE, users.get_current_user(),
          str(event.key))

      self.messages.append("updated")

    else:
      event = None

    self.display['event'] = event
    self.display['EVENT_TYPES'] = db_event.EVENT_TYPES

    self.generate('events/event_add.tmpl')

PUBLISH_WHITELIST = set([
    'joe@aaco-sf.org',
])
class EventOutPage(base.BaseRequestHandler):
  def get(self):
    if not users.is_current_user_admin() \
        or users.get_current_user().email() in PUBLISH_WHITELIST:
      self.errors.append("operation not allowed")
      self.generate("events/index.tmpl", {})
      return

    events = db_event.get_active_events_by_end_date(datetime.datetime.today(),
        TWO_MONTH_DELTA)
    events = filter(lambda e: not e.flag_is_draft, events)

    self.generate('events/event_out.tmpl', {
      'events': events,
      'debug_info': str(events),
    })

  def post(self):
    def _cmp_events(x,y):
      if x.type == y.type:
        return cmp(min(x.starts), min(y.starts))
      else:
        return cmp(x.type, y.type)

    if not users.is_current_user_admin() \
        or users.get_current_user().email() in PUBLISH_WHITELIST:
      self.errors.append("operation not allowed")
      self.generate("events/index.tmpl", {})
      return

    events = sorted(db_event.get_publishable_events(self.request.get_all('key')),
        cmp=_cmp_events)
    tmpl_display = { 'events': events }
    out_html = base.render_tmpl('events/out_html_email.tmpl', tmpl_display)
    out_text = string.strip(base.render_tmpl('events/out_text_email.tmpl',
        tmpl_display))

    if not self.request.get('preview'):

      db_event.clear_all_published()
      db_event.set_multiple_published(self.request.get_all('key'))

      subject = "AACO News: %s" % datetime.datetime.now().strftime("%m/%d/%Y")
      mail.send_mail(
        sender="aacosf@aaco-sf.org", to="AACO-SF@yahoogroups.com",
        #subject=subject, body=out_text, html=out_html)
        subject=subject, body=out_text)

      db_log.log_action(db_log.ACTION_PUBLISH, users.get_current_user(),
          str(self.request.get_all('key')))

      gcal.update_events(itertools.imap(
          lambda e: (e, base.render_tmpl('shared/out_text_item.tmpl', {'event': e})),
              db_event.get_events(self.request.get_all('key'))))

      self.messages.append("done. sent for approval.")

    self.display['events'] = events
    self.generate('events/event_out_preview.tmpl')

def main():
  try:
    application = webapp.WSGIApplication([
      ('/events/', EventIndexPage),
      ('/events/list', EventListPage),
      ('/events/add', EventAddPage),
      ('/events/edit', EventEditPage),
      ('/events/out', EventOutPage),
    ], debug=base._DEBUG)
    wsgiref.handlers.CGIHandler().run(application)

  except Exception, e:
    logging.error("Top-Level Exception: %s", e)
    raise


if __name__ == '__main__':
  main()
