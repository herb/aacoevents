import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


# Set to true if we want to have our webapp print stack traces, etc
_DEBUG = True

class BaseRequestHandler(webapp.RequestHandler):
  """Supplies a common template generation function.

  When you call generate(), we augment the template variables supplied with
  the current user in the 'user' variable and the current webapp request
  in the 'request' variable.
  """

  def __init__(self, request, response):
    super(BaseRequestHandler, self).__init__(request, response)

    self.messages = []
    self.errors = []
    self.display = {}

  def start(self):
    pass

  def generate(self, template_name, template_values={}):
    values = {
      'request': self.request,
      'user': users.get_current_user(),
      'login_url': users.CreateLoginURL(self.request.uri),
      'logout_url': users.CreateLogoutURL('http://' + self.request.host + '/'),
      'messages': self.messages,
      'errors': self.errors,
      'debug': self.request.get('deb'),
      'application_name': 'Event Manager',
    }

    values.update(self.display)
    values.update(template_values)
    #self.response.out.write(render_tmpl(template_name, values))
    import logging; logging.warning('rendered: type(body)={}'.format(type(render_tmpl(template_name, values))))
    self.response.write(str(render_tmpl(template_name, values)))

    # TODO(herb): NEXT: figure out how relative template includes work


def render_tmpl(template_name, values):
  path = os.path.join(os.path.dirname(__file__), '..', 'templates', 
          template_name)

  return template.render(path, values, debug=_DEBUG)
