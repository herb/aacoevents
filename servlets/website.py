import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from db import db_event
from servlets import base


# Add our custom Django template filters to the built in filters
template.register_template_library('filters')

class UpcomingPage(base.BaseRequestHandler):
  def get(self):
    self.display['events'] = filter(
        lambda e: e.type == db_event.EVENT_TYPE_VOLUNTEER,
        db_event.get_published_events())

    self.generate('website/upcoming.tmpl')

class CommunityPage(base.BaseRequestHandler):
  def get(self):
    self.display['events'] = filter(
        lambda e: e.type == db_event.EVENT_TYPE_COMMUNITY,
        db_event.get_published_events())

    self.generate('website/community.tmpl')

def main():
  try:
    application = webapp.WSGIApplication([
      ('/s/upcoming.html', UpcomingPage),
      ('/s/community.html', CommunityPage),
    ], debug=base._DEBUG)
    wsgiref.handlers.CGIHandler().run(application)

  except Exception, e:
    logging.error("Top-Level Exception: %s", e)
    raise


if __name__ == '__main__':
  main()
