from jira import JIRA
from jira.client import ResultList
from jira.resources import Issue
from dotenv import load_dotenv
import os
import datetime
import json
import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

load_dotenv()
my_email=os.getenv('MY_EMAIL')
jira_api=os.getenv('JIRA')
jira_server=os.getenv('JIRA_SERVER')
jiraOptions = {'server': jira_server}
jira=JIRA(options=jiraOptions, basic_auth=(my_email, jira_api))        

#Query linked ServiceNow ticket Number and link
snow_JQL = "project=REPORT AND TYPE=Task AND updatedDate > startofDay('-8d')"
snow_issues=jira.search_issues(snow_JQL, maxResults=0)
snow_issue_dict={}
item = 1  
for snow_issue in snow_issues:
    if len(jira.remote_links(snow_issue))==0:
        continue
    snow_issue_link=vars(jira.remote_links(snow_issue)[0])['raw']['object']['url']
    snow_issue_ticket=vars(jira.remote_links(snow_issue)[0])['raw']['object']['title']
    snow_issue = snow_issue.key

    snow_issue_dict[item] = {
    'SNOW Link': snow_issue_link,
    'Ticket No': snow_issue_ticket,
    'Issue': snow_issue
     }
    item = item + 1
    
df_snow_issues = pd.DataFrame.from_dict(snow_issue_dict, orient='index', columns=['Issue','Ticket No','SNOW Link'])

#Query issue details
strJQL = "project=REPORT AND updatedDate > startofDay('-8d')"
issues=jira.search_issues(strJQL, maxResults=0)
df_issue_details=pd.DataFrame()
for issue in issues:
    issue_dict=jira.issue(issue.key).raw['fields']
    df_issue=pd.json_normalize(issue_dict)
    df_issue['Issue']=issue.key
    df_issue_details=df_issue_details._append(df_issue)
  
df_issue_clean= df_issue_details[['statuscategorychangedate', 'timespent',  'resolutiondate',  'workratio',  'lastViewed',  'created',  'labels',  
 'updated', 'description', 'customfield_10008', 'customfield_10009',  'summary',  'issuetype.name', 'parent.key', 'priority.name',
 'assignee.displayName', 'status.name', 'status.statusCategory.name', 'creator.displayName', 'reporter.displayName', 'aggregateprogress.progress', 'aggregateprogress.total', 'progress.progress', 'progress.total', 'Issue',
 'aggregateprogress.percent', 'progress.percent', 'resolution.name','customfield_10051']]

df_issue_clean.columns=['Status Change Date', 'Time Spent',    'Resolutiondate',  'Work Ratio',  'Last Viewed',  'Created',  'Labels',  
 'Updated',  'Description', 'Actual Start', 'Actual End',  'Summary', 'Issue Type', 'Parent', 'Priority',
 'Assignee', 'Status', 'Status Category', 'Creator','Reporter', 'Aggregate Progress', 'Aggregate Progress Total', 'Progress', 'Progress Total', 'Issue',
  'Aggregate Progress Percent', 'Progress Percent',   'Resolution Name','Request Received']

#Query issue change history
log_JQL = "project=REPORT AND TYPE=Task AND updatedDate > startofDay('-8d')"
log_issues=jira.search_issues(log_JQL, expand='changelog', maxResults=0)
log_issue_dict={}
count = 1  
for log_issue in log_issues:
    histories=log_issue.changelog.histories
    for history in histories:
        change_date=history.created
        items=history.items
        for item in items:
            if item.field == 'status':
                from_status=item.fromString
                to_status = item.toString 
                
                log_issue_dict[count] = {
                'Change Date': change_date,
                'From': from_status,
                'To': to_status,
                'Issue': log_issue.key
                 }
                count = count + 1
    
df_log_issues = pd.DataFrame.from_dict(log_issue_dict, orient='index', columns=['Change Date','From','To','Issue'])
