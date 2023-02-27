#!/usr/bin/env python 

import os
import subprocess
import re
import json
import logging
import logging.handlers
import argparse
from datetime import datetime
import dateutil.parser as dp
import pytz
import requests

def setup_logging(logfile):
  '''
  Setup logging to a file.
  @param logfile: The path to the log file.
  @return: The logger object.
  '''
  # delete any existing file
  if os.path.exists(logfile):
    os.remove(logfile)
  # Setup logging
  logger = logging.getLogger('log_commits')
  logger.setLevel(logging.DEBUG)
  # log to stdout
  # ch = logging.StreamHandler()
  # logger.addHandler(ch)
  # log to file
  fh = logging.handlers.RotatingFileHandler(logfile, maxBytes=1000000, backupCount=5)
  fh.setLevel(logging.DEBUG)
  logger.addHandler(fh)    
  return logger

def get_exclusions(filename):
  '''
  Get a list of files to exclude from analysis.
  @param filename: The path to the file containing the list of files to exclude.
  @return: A list of files to exclude.
  '''
  with open(filename) as file:
    lines = [line.strip() for line in file]
    return lines

def get_args():
  '''
  Parse command-line arguments.
  @return: The parsed arguments.
  '''

  # default files to exclude from analysis
  current_dir = os.path.dirname(os.path.realpath(__file__)) # the current directory
  exclusion_file = os.path.join(current_dir, '.logsignore')
  exclusions = get_exclusions(exclusion_file)

  # parse command-line arguments
  parser = argparse.ArgumentParser()
  parser.add_argument("-r", "--repository_url", help="URL of the github repository upon which this logger is being run", default='', required=False)
  parser.add_argument("-t", "--event_type", help="The type of event that is triggering this logger to be run, e.g. 'push' or 'pull_request', from github.event_type.", default='', required=False)
  parser.add_argument("-d", "--event_date", help="The date the event is being triggered.", default='', required=False)
  parser.add_argument("-un", "--user_name", help="The name of the user performing the event.", default='', required=False)
  parser.add_argument("-ue", "--user_email", help="The email of the user performing the event.", default='', required=False)
  parser.add_argument("-i", "--inputfile", help="filename of JSON array of commits (typically saved from GitHub Action context variable, github.event.commits, during push events.)", default='', required=False)
  parser.add_argument("-o", "--outputfile", help="filename where to store the CSV output with git stats for each commit.", default='', required=True)
  parser.add_argument("-u", "--url", help="The URL of the web app where the commit stats should be sent.", default='')
  parser.add_argument("-x", "--exclusions", help='A comma-separated string of files to exclude, e.g. --excusions "foo.zip, *.jpg, *.json" ', default=','.join(exclusions))
  parser.add_argument("-v", "--verbose", help="Whether to output debugging info", default=False, action="store_true")
  args = parser.parse_args()

  # fix up exclusions
  args.exclusions = re.split(r',\s*', args.exclusions) # split up comma-separated string into list
  return args

def get_commit_ids(commit_datafile):
  '''
  Load commit ids from file.
  @param commit_datafile: The path to the file containing the JSON array of commits.

  '''
  # load commit ids from file
  with open(commit_datafile, 'r') as commitfile:
    commits_list = json.loads(commitfile.read()) # convert to list
    # print(f'commits_list: {commits_list}')
    commit_ids = [commit['id'] for commit in commits_list if 'id' in commit.keys()] # extract commit ids from data from the GitHub Action context variable
    # print(f'commit_ids: {commit_ids}')
    return commit_ids

def get_git_output(commit_id, exclusions):
  # print(f'commit id: {commit_id}')
  date_format = r'--date=unix' #format:"%m/%d/%Y %H:%M" # formatted in a way that works well in Google Sheets
  cmd = f"git show {date_format} --shortstat {commit_id} {exclusions}"
  # print(f'command: {cmd}')
  git_log = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  git_log_out, git_log_err = git_log.communicate()
  git_log_out = git_log_out.decode('UTF-8') # convert bytes to string
  # print(f'git output: {git_log_out}')
  # print(f'git error: {git_log_err}')
  return git_log_out.strip(), git_log_err.strip()

def get_commit_data(git_log_out):
  '''
  Get git stats for a commit.
  @param commit_id: The commit id.
  @param exclusions: The files to exclude from the git stats.
  @return: A dictionary containing the git stats for the commit.
  '''
  # parse git commit log
  commit_data = {} # start off blank
  m = re.match(r"commit ([a-zA-Z0-9]+).*\nAuthor:\s(.*)\s<((.*))>.*\nDate:\s(.*)\n\n(.*)\n\n(.*?(\d+) file[s]? changed)?(.*?(\d+) insertion[s]?)?(.*?(\d+) deletion[s]?)?", git_log_out)
  if not m is None:
    # basic commit info
    commit_data['id'] = m.groups(0)[0].strip()
    commit_data['author_name'] = m.groups(0)[1].strip()
    commit_data['author_email'] = m.groups(0)[2].strip()
    commit_data['date'] = m.groups(0)[4].strip()
    commit_data['message'] = m.groups(0)[5].replace('[,"]', '').strip() # remove any quotes and commas to make a valid csv
    # fix the date
    commit_data['date'] = fix_date(commit_data['date'])
    # stats
    commit_data['files'] = m.groups(0)[7].strip()
    commit_data['additions'] = m.groups(0)[9].strip() if len(m.groups(0)) > 9 and type(m.groups(0)[9])==str else 0
    commit_data['deletions'] = str(m.groups(0)[11]).strip() if len(m.groups(0)) > 11 and type(m.groups(0)[11])==str else 0
  # print(f'commit_data: {commit_data}')
  return commit_data

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

def verboseprint(verbose, *args):
  '''
  Print only if verbose flag is set.
  '''
  if verbose:
      v = print
  else:
      v = lambda *args: None
  v(*args)

def main():

  # set up command line arguments
  args = get_args()

  # set up logging
  logger = setup_logging(args.outputfile)

  # set up exclusions
  exclusions = '-- . ' + ' '.join(["':(exclude,glob){}'".format(x) for x in args.exclusions]) # put the exclusions in the format git logs uses
  # print(f'exclusions: {exclusions}')

  # write the CSV heading line
  logger.info('repository_url,event_type,commit_id,commit_author_name,commit_author_email,commit_date,commit_message,commit_files,commit_additions,commit_deletions')
  
  events_list = [] # start it off blank

  # get pull request data, if any supplied
  if args.event_type in ['pull_request_opened', 'pull_request_merged', 'pull_request_closed']:
    # get pull request data
    pull_request_data = {
      'repository_url': args.repository_url,
      'event_type': args.event_type,
      'id': '',
      'author_name': args.user_name,
      'author_email': args.user_email,
      'date': fix_date(args.event_date),
      'message': '',
      'files': '',
      'additions': '',
      'deletions': ''
    }

    # add this pull request to the list
    events_list.append(pull_request_data)

  # get push data, if any supplied
  elif args.event_type in ['push']:

    # get ids of each commit, if any supplied
    commit_ids = []
    if args.inputfile:
      commit_ids = get_commit_ids(args.inputfile) # get the ids of all commits from the json file

    # iterate over commit ids, if any, and add each to a list
    for commit_id in commit_ids:

      # get git output for this commit
      git_log_out, git_log_err = get_git_output(commit_id, exclusions)
      verboseprint(args.verbose, f'git output: {git_log_out}') # raw output
      verboseprint(args.verbose, f'git err: {git_log_err}') # any errors

      # handle missing commit data... this seems to occur with merge commits
      if git_log_out == '':
        verboseprint(args.verbose, f'empty git output... skipping')
        continue

      # parse git output
      commit_data = get_commit_data(git_log_out) 
      if not bool(commit_data):
        verboseprint(args.verbose, f'empty parsed data... skipping')
        continue
      verboseprint(args.verbose, f'parsed git stats: {commit_data}')

      # add repository url, if present
      if args.repository_url:
        # verboseprint(args.verbose, f'repository_url: {args.repository_url}')
        commit_data['repository_url'] = args.repository_url

      # add event type, if present
      if args.event_type:
        # verboseprint(args.verbose, f'event_type: {args.event_type}')
        commit_data['event_type'] = args.event_type

      # add this commit to the list
      events_list.append(commit_data) 
      
      # log it to the csv data file
      logger.info(f'{args.repository_url},{commit_data["event_type"]},{commit_id},{commit_data["author_name"]},{commit_data["author_email"]},{commit_data["date"]},"{commit_data["message"]}",{commit_data["files"]},{commit_data["additions"]},{commit_data["deletions"]}')

  # debugging print
  verboseprint(args.verbose, f'events list: {events_list}')

  # send the data to the web app URL, if any was supplied
  if args.url:
    # convert the list of commits to a JSON string
    commits_json = json.dumps(events_list)
    # send the data to the web app in a POST request
    r = requests.post(args.url, json=events_list)
    verboseprint(args.verbose, 'web app response: ', r.status_code, r.reason, r.content, r.text) # really the one

if __name__ == "__main__":
  main()
