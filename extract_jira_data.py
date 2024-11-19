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

#Query Epics details
epicJQL = "project=REPORT AND type=Epic"
epics=jira.search_issues(epicJQL, maxResults=0)
df_epic_details=pd.DataFrame()
for epic in epics:
    epic_dict=jira.issue(epic.key).raw['fields']
    df_epic=pd.json_normalize(epic_dict)
    df_epic['Epic']=epic.key
    df_epic_details=df_epic_details._append(df_epic)

df_epic_clean= df_epic_details[['created',  'labels',  'updated', 'description','customfield_10053.value','customfield_10054.value', 'customfield_10056.value', 'summary',  'assignee.displayName','status.name','priority.name','Epic']]
df_epic_clean.columns=['Created',  'Labels',  'Updated',  'Description',  'Report Tool' ,'Backup', 'Workspace','Summary', 'Assignee','Status', 'Priority','Epic']    

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

#Query time spend
logJQL = "project=REPORT AND TYPE=Task"
issues=jira.search_issues(logJQL, maxResults=0)
worklogs_dict = {}
item = 1
for issue in issues:
    issue_id = issue.key
    for worklog in issue.fields.worklog.worklogs:
        
        # Initialize variables to None
        author = time_spent = comment = created = None
        
        # Check if 'author' exists
        if hasattr(worklog.author, 'displayName') and worklog.author.displayName:
            author = worklog.author.displayName
        
        # Check if 'timeSpent' exists
        if hasattr(worklog, 'timeSpentSeconds') and worklog.timeSpentSeconds:
            time_spent = worklog.timeSpentSeconds
        
        # Check if 'comment' exists (this attribute might not be present)
        if hasattr(worklog, 'comment') and worklog.comment:
            comment = worklog.comment
        
        # Check if 'created' exists
        if hasattr(worklog, 'created') and worklog.created:
            created = worklog.created
            
        # Check if 'started' exists
        if hasattr(worklog, 'started') and worklog.started:
            started = worklog.started    

        # Check if 'updated' exists
        if hasattr(worklog, 'updated') and worklog.updated:
            updated = worklog.updated             
        
        # Proceed only if all necessary fields are present
            worklogs_dict[item] = {
                'Author': author,
                'Time Spent': time_spent,
                'Comment': comment,
                'Created': created,
                'Started': started,          
                'Updated': updated,                
                'Issue': issue_id
            }
            item += 1
df_worklogs = pd.DataFrame.from_dict(worklogs_dict, orient='index', columns=['Author','Time Spent','Comment','Created','Started','Updated','Issue']) 

#Query Weblink
link_JQL = "project=REPORT AND TYPE in (Task, Epic) "
link_issues=jira.search_issues(link_JQL, maxResults=0)
link_dict={}
item = 1  
for link_issue in link_issues:
    if len(jira.remote_links(link_issue))==0:
        continue
    link=vars(jira.remote_links(link_issue)[0])['raw']['object']['url']
    link_text=vars(jira.remote_links(link_issue)[0])['raw']['object']['title']
    link_issue = link_issue.key

    link_dict[item] = {
    'URL': link,
    'Link Text': link_text,
    'Issue': link_issue
     }
    item = item + 1 
df_links = pd.DataFrame.from_dict(link_dict, orient='index', columns=['Issue','Link Text', 'URL'])
df_links.to_csv('C:/Users/azheng/Downloads/Python/links.csv', mode='w', index=False)
