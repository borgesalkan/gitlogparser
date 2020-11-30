import csv
import re
import argparse
import dateutil.parser
from collections import defaultdict

"""
Get your git log stats with the following command:
    git log --stat >> git-log-stats.txt
    
Then run this programs as:
    python git_log_stats_parser.py --logfile git-log-stats.txt --csvfile git-logs-stats.csv
    
You'll have all the stats in csv format.

"""


class GitLogStatsParser:

    def parse_commit_stats(self, git_log_file: str, out_csv_file: str):

        log_file = open(git_log_file)
        commit_log_lines = log_file.readlines()

        commit_dict = defaultdict(dict)
        curr_commit_id = None
        for commit_log_line in commit_log_lines:

            if commit_log_line.strip() == '' or commit_log_line == '\n':
                # Skip blank lines
                pass

            elif bool(re.match('commit', commit_log_line, re.IGNORECASE)):
                # commit a1b2c3
                curr_commit_id = re.match('commit (.*)', commit_log_line, re.IGNORECASE).group(1)
                commit_dict[curr_commit_id] = dict()
                commit_dict[curr_commit_id]['commit'] = curr_commit_id

            elif bool(re.match('author:', commit_log_line, re.IGNORECASE)):
                # Author: William B. <email@web.com>
                author_name, author_email = re.compile('Author: (.*) <(.*)>').match(commit_log_line).groups()
                commit_dict[curr_commit_id]['author'] = author_name
                commit_dict[curr_commit_id]['email'] = author_email

            elif bool(re.match('date:', commit_log_line, re.IGNORECASE)):
                # Date: Mon Jan 1 10:30:14 2019 -0800
                dt_str = re.match('Date: (.*)', commit_log_line, re.IGNORECASE).group(1)
                dt_isoformat_str = dateutil.parser.parse(dt_str).isoformat('T', 'seconds')
                commit_dict[curr_commit_id]['date'] = dt_isoformat_str

            elif bool(re.match('\s.*\|[\s]*[\d]*\s.*', commit_log_line)):
                # Commit log line has file name and number of changes
                pass

            elif bool(re.match('.*files? changed.*', commit_log_line, re.IGNORECASE)):
                files_changed, insertions, deletions = 0, 0, 0
                sections = commit_log_line.split(', ')
                for section in sections:
                    section = section.strip()
                    if bool(re.match('(\d*) files? changed.*', section)):
                        files_changed = int(re.match('(\d*) files? changed.*', section).groups()[0])
                    elif bool(re.match('(\d*) insertion.*', section)):
                        insertions = int(re.match('(\d*) insertion.*', section).groups()[0])
                    elif bool(re.match('(\d*) deletion.*', section)):
                        deletions = int(re.match('(\d*) deletion.*', section).groups()[0])

                commit_dict[curr_commit_id]['files_changes'] = files_changed
                commit_dict[curr_commit_id]['insertions'] = insertions
                commit_dict[curr_commit_id]['deletions'] = deletions

            elif bool(re.match('    ', commit_log_line, re.IGNORECASE)):
                # If 4 empty spaces then commit message line. Storing only the title. No desc.
                if commit_dict[curr_commit_id].get('title') is None:
                    commit_dict[curr_commit_id]['title'] = commit_log_line.strip()
            else:
                print("Error while parsing line: '{}'".format(commit_log_line))

        commits = sorted(commit_dict.values(), key=lambda x: x['date'], reverse=True)
        csv_keys = commits[0].keys()
        
        with open(out_csv_file, 'w', newline="") as csv_file:
            dict_writer = csv.DictWriter(csv_file, fieldnames=csv_keys)
            dict_writer.writeheader()
            dict_writer.writerows(commits)

        print('Wrote logs to CSV file: ' + out_csv_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', help='Input Log File Name')
    parser.add_argument('--csvfile', help='Output CSV File Name')
    args = parser.parse_args()
    GitLogStatsParser().parse_commit_stats(args.logfile, args.csvfile)
