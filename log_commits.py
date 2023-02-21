#!/usr/bin/env python 

def main():
    import sys
    import os
    import subprocess
    import re
    import time
    import datetime
    import json
    import logging
    import logging.handlers

    # Setup logging
    logger = logging.getLogger('log_commits')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.handlers.RotatingFileHandler('log_commits.log', maxBytes=1000000, backupCount=5)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)    

    # Get the current directory
    current_dir = os.getcwd()

    # Get the git log
    commit_ids = ['482d0d1842a25e3f564aec39c4bf879b95e7fe02', '04c3a74f3b3405fac6bc27368a0a516225139b80', 'eda541d6ba86bcf2c9c1eebb67f208044aafc896']
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
