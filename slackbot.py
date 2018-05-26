from __future__ import print_function
from slackclient import SlackClient
from collections import OrderedDict
from apiclient.discovery import build
from apiclient import errors
from httplib2 import Http
from oauth2client import file, client, tools
import requests
import os
import json
import sys
import imaplib
import getpass
import email
import email.header
import datetime

EMAIL_ACCOUNT = "Blockchainportfoliomanagment@gmail.com"

# Use 'INBOX' to read inbox.  Note that whatever folder is specified, 
# after successfully running this script all emails in that folder 
# will be marked as read.
EMAIL_FOLDER = "INBOX"
token = os.environ.get('SLACKBOT_TOKEN')

def process_mailbox(M):
    """
    Do something with emails messages in the folder.  
    For the sake of this example, print some headers.
    """

    rv, data = M.search(None, "ALL")
    if rv != 'OK':
        print("No messages found!")
        return

    for num in data[0].split():
        rv, data = M.fetch(num, '(RFC822)')
        if rv != 'OK':
            print("ERROR getting message", num)
            return

        msg = email.message_from_bytes(data[0][1])
        body = msg.get_payload()
        hdr = email.header.make_header(email.header.decode_header(msg['Subject'])[0])
        subject = str(hdr)
        print('Message %s: %s' % (num, subject))
        print('Message body: ' + body)
        print('Raw Date:', msg['Date'])
        # Now convert to local date-time
        date_tuple = email.utils.parsedate_tz(msg['Date'])
        if date_tuple:
            local_date = datetime.datetime.fromtimestamp(
                email.utils.mktime_tz(date_tuple))
            print ("Local Date:", \
                local_date.strftime("%a, %d %b %Y %H:%M:%S"))

def print_email_headers():           
	M = imaplib.IMAP4_SSL('imap.gmail.com')

	try:
	    rv, data = M.login(EMAIL_ACCOUNT, getpass.getpass())
	except imaplib.IMAP4.error:
	    print ("LOGIN FAILED!!! ")
	    sys.exit(1)

	print(rv, data)

	rv, mailboxes = M.list()
	if rv == 'OK':
	    print("Mailboxes:")
	    print(mailboxes)

	rv, data = M.select(EMAIL_FOLDER)
	if rv == 'OK':
	    print("Processing mailbox...\n")
	    process_mailbox(M)
	    M.close()
	else:
	    print("ERROR: Unable to open mailbox ", rv)

	M.logout()

def get_market_data(ticker):
	request_url = "https://api.binance.com/api/v1/ticker/24hr?symbol=" + ticker 
	r = requests.get(request_url)
	response = json.loads(r.text, object_pairs_hook=OrderedDict)
	myObject = {
		"symbol" : response['symbol'], 
		"24HrChangePercent" : response['priceChangePercent'], 
		"lastPrice" : response['lastPrice'],
		"24HourHigh" : response['highPrice'],
		"24HourLow" : response['lowPrice'],
		"quoteVolume" : response['quoteVolume'],
		}
	return(myObject)


def slack_message(message, channel):
    sc = SlackClient(token)
    sc.api_call('chat.postMessage', channel=channel, 
                text=message, username='pythonbot',
                icon_emoji=':robot_face:')

def gmail_setup():
	SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
	store = file.Storage('credentials.json')
	creds = store.get()
	if not creds or creds.invalid:
	    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
	    creds = tools.run_flow(flow, store)
	service = build('gmail', 'v1', http=creds.authorize(Http()))
	return service

def gmail_exec(service):
	results = service.users().labels().list(userId='me').execute()
	labels = results.get('labels', [])
	if not labels:
	    print('No labels found.')
	else:
	    print('Labels:')
	    for label in labels:
	        print(label['name'])

if __name__ == "__main__":
	print_email_headers()
	# service = gmail_setup()
	# gmail_exec(service)

    # slack_message(get_market_data("ETHBTC"), "cmc-alerts")