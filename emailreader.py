from __future__ import print_function
import os.path
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://mail.google.com/', 'https://www.googleapis.com/auth/gmail.modify']


def authenticate():
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
      token.write(creds.to_json())
  return creds


def fetch_emails(service, query):
  # Get a list of 500 or less emails based on the given query
  response = service.users().messages().list(
    userId='me',
    q=query,
    maxResults=500).execute()
  message_ids = []
  if "messages" in response:
    for message in response["messages"]:
      message_ids.append(message["id"])
  # Retrieve more messages if there are more that match the query
  while "nextPageToken" in response and len(message_ids) < 1000:
    token = response["nextPageToken"]
    response = service.users().messages().list(
      userId='me',
      q=query,
      maxResults=500,
      pageToken=token).execute()
    if "messages" in response:
      for message in response["messages"]:
        message_ids.append(message["id"])
  return message_ids


def mark_as_read(service, messages):
  body = {
    "ids": messages,
    "addLabelIds": [],
    "removeLabelIds": ["UNREAD"]
  }
  service.users().messages().batchModify(
    userId='me',
    body=body
  ).execute()


def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """

  # Login to gmail
  creds = authenticate()

  try:
    # Call the Gmail API
    service = build('gmail', 'v1', credentials=creds)
    query = sys.argv[1]
    # Get list of messages that match the query
    print("fetching emails...")
    message_list = fetch_emails(service, query)
    print(f"{len(message_list)} emails fetched!\n")
    # Mark emails as read
    print("marking emails as read...\n")
    mark_as_read(service, message_list)
    # Mark emails as read until there are no more unread
    total_read = len(message_list)
    while True:
      # Fetch emails
      print("fetching emails...")
      message_list = fetch_emails(service, query)
      print(f"{len(message_list)} emails fetched!\n")
      # Stop if there are no unread emails
      if not message_list:
        break
      # Mark as read
      print("marking emails as read...\n")
      mark_as_read(service, message_list)
      total_read += len(message_list)      
    
    print(f"{total_read} emails marked as read!")

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()