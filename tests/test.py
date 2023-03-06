import re
from datetime import datetime
import dateutil.parser as dp
import pytz

def fix_date(bad_date):
  '''
  Fix the date format to be easier to parse by Google Sheets
  @param date: The date to fix, either in unix time or ISO format
  @return: The fixed date in a format that works well in Google Sheets
  '''
  try:
    # date from git commits is in unix time
    bad_date_int = int(bad_date)
  except ValueError:
    # date from github actions context is in ISO format
    iso_date = bad_date
    parsed_t = dp.parse(iso_date)
    bad_date_int = int(parsed_t.strftime('%s'))

  local_tz = pytz.timezone("America/New_York")
  utc_time = datetime.utcfromtimestamp(bad_date_int) # convert unix time to utc datetime
  tz_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_tz) # convert to NY time
  good_date = tz_time.strftime('%m/%d/%Y %H:%M') # formatted as nice string good for Google Sheets date field
  return good_date


f = open('./test_commit3.txt')
git_log_out = f.read()
git_log_out = re.sub("(\n {4}(.+)\n)+", r"\1", git_log_out) # remove multi-line commit messages
m = re.match(r"commit ([a-zA-Z0-9]+).*\n(Merge:\s.*\n)?Author:\s(.*)\s<((.*))>.*\nDate:\s(.*)\n+(.*?)\n+(.*?(\d+) file[s]? changed)?(.*?(\d+) insertion[s]?)?(.*?(\d+) deletion[s]?)?", git_log_out)

print(git_log_out)

commit_data = {}
if not m is None:
  print()
  print('num matches:', len(m.groups(0)))
  print()
  print('matches:', m.groups(0))
  print()
  # basic commit info
  commit_data['id'] = m.groups(0)[0].strip()
  commit_data['author_name'] = m.groups(0)[2].strip()
  commit_data['author_email'] = m.groups(0)[3].strip()
  commit_data['date'] = m.groups(0)[5].strip()
  commit_data['message'] = m.groups(0)[6].replace('[,"]', '').strip() # remove any quotes and commas to make a valid csv
  # fix the date
  commit_data['date'] = fix_date(commit_data['date'])
  # stats
  commit_data['files'] = m.groups(0)[8].strip() if type(m.groups(0)[8]) == str else m.groups(0)[8]
  commit_data['additions'] = m.groups(0)[10].strip() if len(m.groups(0)) > 10 and type(m.groups(0)[10])==str else 0
  commit_data['deletions'] = str(m.groups(0)[12]).strip() if len(m.groups(0)) > 12 and type(m.groups(0)[12])==str else 0
  print(f'commit_data: {commit_data}')
else:
  # print(git_log_out)
  pass
