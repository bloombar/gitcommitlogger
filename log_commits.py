#!/usr/bin/env python 

import subprocess
import re
import json
import logging
import logging.handlers
import argparse

def setup_logging(logfile):
  '''
  Setup logging to a file.
  @param logfile: The path to the log file.
  @return: The logger object.
  '''
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

def get_args():
  '''
  Parse command-line arguments.
  @return: The parsed arguments.
  '''
  # parse command-line arguments
  parser = argparse.ArgumentParser()
  parser.add_argument("-c", "--commitfile", help="filename of JSON array of commits from GitHub Action context variable, github.event.commits", default='', required=True)
  parser.add_argument("-u", "--url", help="The URL of the web app where the commit stats should be sent.", default='')
  args = parser.parse_args()
  return args

def main():

  # set up logging
  logger = setup_logging('data.csv')

  # set up command line arguments
  parser = get_args()

  # Get the git log
  # load commit ids from file
  with open(parser.commitfile, 'r') as commitfile:
    commit_data = commitfile.read()
    commit_ids = [commit['id'] for commit in json.loads(commit_data)] # extract commit ids from data from the GitHub Action context variable
    print(commit_ids)
  logger.info('commit_id,commit_author_name,commit_author_email,commit_date,commit_message,commit_files,commit_additions,commit_deletions')
  for commit_id in commit_ids:
    # get git stats for this commit
    cmd = f"git show --shortstat {commit_id}" #--date=format-local:'%m/%d/%Y %H:%M:%S'"
    git_log = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    git_log_out, git_log_err = git_log.communicate()
    git_log_out = git_log_out.decode('UTF-8') # convert bytes to string

    # parse git commit log
    m = re.match(r"commit ([a-zA-Z0-9]+).*\nAuthor:\s(.*)\s<((.*))>.*\nDate:\s(.*)\n\n(.*)\n\n(.*?(\d+) file[s]? changed)?(.*?(\d+) insertion[s]?)?(.*?(\d+) deletion[s]?)?", git_log_out)
    if not m is None:
      # basic commit info
      commit_id = m.groups(0)[0].strip()
      commit_author_name = m.groups(0)[1].strip()
      commit_author_email = m.groups(0)[2].strip()
      commit_date = m.groups(0)[4].strip()
      commit_message = m.groups(0)[5].replace('[,"]', '').strip() # remove any quotes and commas to make a valid csv
      # stats
      commit_files = m.groups(0)[7].strip()
      commit_additions = m.groups(0)[9].strip() if len(m.groups(0)) > 9 else 0
      commit_deletions = str(m.groups(0)[11]).strip() if len(m.groups(0)) > 11 else 0
      # print(f"{commit_id},{commit_author_name},{commit_author_email},{commit_date},{commit_message},{commit_files},{commit_additions},{commit_deletions}")
      logger.info(f'{commit_id},{commit_author_name},{commit_author_email},{commit_date},"{commit_message}",{commit_files},{commit_additions},{commit_deletions}')
    else:
      # print('no match')
      pass

if __name__ == "__main__":
  main()
