#!/usr/bin/env python

""" This program is originally from the following stackoverflow thread:
http://stackoverflow.com/questions/348630/how-can-i-download-all-emails-with-attachments-from-gmail

Only minor modifications by Carl Sandrock
"""

import email
import imaplib
import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

if len(sys.argv) > 1:
    detach_dir = sys.argv[1]
else:
    detach_dir = '.'

overwritefiles = True
askforpassword = False

if askforpassword:
    import getpass
    user = raw_input("Enter your GMail username:")
    pwd = getpass.getpass("Enter your password: ")
else:
    user = "chemeng"
    pwd = "chemeng"

# connecting to the gmail imap server
logging.info('Logging in')
m = imaplib.IMAP4_SSL("mx1.up.ac.za")
m.login(user,pwd)

logging.info('Login successful')
m.select("INBOX") # here you a can choose a mail box like INBOX instead
# use m.list() to get all the mailboxes

resp, items = m.search(None, 'TO', '"csc411@up.ac.za"') # you could filter using the IMAP rules here (check http://www.example-code.com/csharp/imap-search-critera.asp)
items = items[0].split() # getting the mails id

found = 0
written = 0
xlsfiles = set()
for emailid in items:
    resp, data = m.fetch(emailid, "(RFC822)") # fetching the mail, "`(RFC822)`" means "get the whole stuff", but you can ask for headers only, etc
    email_body = data[0][1] # getting the mail content
    mail = email.message_from_string(email_body) # parsing the mail content to get a mail object

    logging.info('Found mail: %s - %s' % (mail["From"], mail["Subject"]))
    found += 1

    #Check if any attachments at all
    if mail.get_content_maintype() != 'multipart':
        logging.info('No attachments - skipping')
        continue

    # we use walk to create a generator so we can iterate on the parts and forget about the recursive headach
    for part in mail.walk():
        # multipart are just containers, so we skip them
        if part.get_content_maintype() == 'multipart':
            continue

        # is this part an attachment ?
        if part.get('Content-Disposition') is None:
            continue

        filename = part.get_filename()
        counter = 1

        # if there is no filename, we create one with a counter to avoid duplicates
        if not filename:
            filename = 'part-%03d%s' % (counter, 'bin')
            counter += 1

        att_path = os.path.join(detach_dir, filename)

        #Check if its already there
        fileexists = os.path.isfile(att_path)
        if overwritefiles or not fileexists:
            # finally write the stuff
            open(att_path, 'wb').write(part.get_payload(decode=True))
            logging.info(('Overwrote ' if fileexists else 'Wrote ') + att_path)
            written += 1
            if filename.endswith('.xls'): xlsfiles.add(filename)
        else:
            logging.warn('Refusing to overwrite existing file ' + att_path)

logging.info('Done.  Found %i mails, wrote %i files. %i seem to be unique .xls files' % (found, written, len(xlsfiles)))
