import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from db import db_event
from servlets import base


# Add our custom Django template filters to the built in filters
template.register_template_library('util.filters')

class UpcomingPage(base.BaseRequestHandler):
  def get(self):
    self.display['events'] = filter(
        lambda e: e.type == db_event.EVENT_TYPE_VOLUNTEER,
        db_event.get_published_events())

    self.display['page_title'] = 'Upcoming Events'
    self.generate('website/upcoming.tmpl')

class CommunityPage(base.BaseRequestHandler):
  def get(self):
    self.display['events'] = filter(
        lambda e: e.type == db_event.EVENT_TYPE_COMMUNITY,
        db_event.get_published_events())

    self.display['page_title'] = 'Community Events'
    self.generate('website/community.tmpl')

class MissionPage(base.BaseRequestHandler):
  def get(self):
    self.display['page_title'] = 'About Us'
    self.generate('website/about.tmpl')

def main():
  try:
    application = webapp.WSGIApplication([
      ('/s/upcoming.html', UpcomingPage),
      ('/s/community.html', CommunityPage),
      ('/s/about.html', MissionPage),
    ], debug=base._DEBUG)
    wsgiref.handlers.CGIHandler().run(application)

  except Exception, e:
    logging.error("Top-Level Exception: %s", e)
    raise


if __name__ == '__main__':
  main()
