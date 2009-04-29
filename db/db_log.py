import datetime
import itertools
import logging

from google.appengine.ext import db

ACTION_CREATE = "C"
ACTION_UPDATE = "U"
ACTION_DELETE = "D"
ACTION_PUBLISH = "P"

#
#
#

class Log(db.Expando):
  action = db.TextProperty(required=True)

  actor = db.UserProperty(required=True)
  target = db.TextProperty(required=True)

  created = db.DateTimeProperty(auto_now_add=True)


#
#
#

def log_action(action, user, target):
  log = Log(action=action, actor=user, target=target)

  db.put(log)
