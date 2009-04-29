import datetime

class US_Pacific(datetime.tzinfo):
 """Implementation of the Pacific timezone. Stolen from App Engine
 documentation."""
 def utcoffset(self, dt):
   return datetime.timedelta(hours=-8) + self.dst(dt)

 def _FirstSunday(self, dt):
   """First Sunday on or after dt."""
   return dt + datetime.timedelta(days=(6-dt.weekday()))

 def dst(self, dt):
   # 2 am on the second Sunday in March
   dst_start = self._FirstSunday(datetime.datetime(dt.year, 3, 8, 2))
   # 1 am on the first Sunday in November
   dst_end = self._FirstSunday(datetime.datetime(dt.year, 11, 1, 1))

   if dst_start <= dt.replace(tzinfo=None) < dst_end:
     return datetime.timedelta(hours=1)
   else:
     return datetime.timedelta(hours=0)

 def tzname(self, dt):
   if self.dst(dt) == datetime.timedelta(hours=0):
     return "PST"
   else:
     return "PDT"

class UTC(datetime.tzinfo):
  def utcoffset(self , dt):
    return datetime.timedelta(hours=0)

  def dst(self, dt):
    return datetime.timedelta(hours=0)

  def tzname(self, dt):
    return "UTC"

utc = UTC()
us_pacific = US_Pacific()
