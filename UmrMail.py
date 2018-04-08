#!/usr/bin/python3
# -*- coding: utf-8 -*-

#Umr imports
from UmrConf import gconfig
import UmrIcal
#messaging
import poplib, email, smtplib
#parse and compose
import email.parser, email.policy, email.mime.text
import re
import html2text, html
#sys
import logging
import sys

COMMASPACE = ", "
cpop = None #pop handle
csmtp = None #smtp handle

def connectPop():
    """Connect to pop server and return connection handler"""
    global cpop
    if cpop != None : #already connected ?
        return(cpop)
    #get config
    serverssl = gconfig.get("Mail", 'serverssl')
    portssl = int(gconfig.get("Mail", 'portssl'))
    username = gconfig.get("Mail", 'username')
    password = gconfig.get("Mail", 'password')
    #connecting
    logging.debug("Connecting to %s:%d with user %s", serverssl, portssl, username)
    cpop = poplib.POP3_SSL(serverssl,portssl)
    cpop.user(username)
    cpop.pass_(password)
    #FIXME : test something ?
    return(cpop)

def connectSmtp():
    """Connect to SMTP server with credentials"""
    global csmtp #global var
    if csmtp != None: #already defined
        return(csmtp)
    #get config
    serversmtp = gconfig.get("Mail", 'serversmtp')
    portsmtp = gconfig.getint("Mail", 'portsmtp')
    username = gconfig.get("Mail", 'username')
    password = gconfig.get("Mail", 'password')
    #connecting
    logging.debug("Connecting to SMTP %s:%d with user %s", serversmtp, portsmtp, username)
    csmtp = smtplib.SMTP_SSL(serversmtp, portsmtp) #connecting
    csmtp.login(username, password) #login
    return(csmtp)

def fetchMails():
    """Fetch mail with POP from inbox in config"""
    cpop = connectPop() #connect if not connected
    nb = int(cpop.stat()[0]) #number of messages
    logging.debug("%s messages found", nb)
    results = []
    if nb > 0 : #something to do
        for i in range(1, nb+1): #for each message
            mp = email.parser.BytesFeedParser(policy=email.policy.default)
            for j in cpop.retr(i)[1]:
                mp.feed(j+b'\r\n')
            fullmail = mp.close()
            #catch sender
            if 'Reply-To' in fullmail:
                sender = fullmail['Reply-To']
            else :
                sender = fullmail['From']
            message = (sender, fullmail)
            results.append(message) #add to results
    return(results)

def disconnect():
    """Disconnect from pop and smtp connexion"""
    cpop = connectPop()
    csmtp = connectSmtp()
    cpop.quit() #close connection, mark messages as read
    csmtp.close()

def makeMimeText(send_to, subject, text):
    """Make MIME object"""    
    assert type(send_to)==list
    #make mail object
    textmsg = email.mime.text.MIMEText(text, _charset='utf-8')        
    #make headers
    textmsg['To'] = COMMASPACE.join(send_to)
    textmsg['Date'] = email.utils.formatdate(localtime=True)
    textmsg['Subject'] = subject
    return(textmsg)

def sendOneMail(send_to, subject, text, files=[]):
    """Send one mail"""
    #message building
    logging.info("Make mail with subject: %s", subject) 
    msg = makeMimeText(send_to, subject, text)
    #sending
    sendSomeMails([msg])

def sendSomeMails(mailList):
    """Send some messages from message list"""
    logging.info("Sending mails")
    csmtp = connectSmtp()
    sender = gconfig.get("Mail", 'sender')
    sendername = gconfig.get("Mail", 'sendername')
    fromtext = '"%s" <%s>' % (sendername, sender)
    #on envoie !
    for msg in mailList:
        logging.info("Sending message to %s", msg['To'])
        msg['From'] = fromtext
        csmtp.sendmail(fromtext, msg['To'], msg.as_string())

def get_content_as_text(emailmessage):
    """Get email as text"""
    part = emailmessage.get_body(preferencelist=('plain'))
    if part == None : #no plain type, try html
        part = emailmessage.get_body(preferencelist=('html'))
        text = part.get_payload(decode=True).decode('UTF-8')
        text = html2text.html2text(text)
    else : #go on with text
        text = part.get_payload(decode=True).decode('UTF-8')
        text = html.unescape(text)
    return(text.strip())

def extract_content(text):
    """Extract useful content between enclosers ===.*==="""
    #FIXME : === enclosers could be in conf ?
    added = None
    for l in text.split("\n") : #extract additions :::
        m = re.match(r':::\s*(.*)', l.strip())
        if m is not None :
            if added is not None :
                added = "%s\n%s" % (added, m.groups()[0])
            else :
                added = m.groups()[0]

    m = re.search(r'===(.*)===', text, re.MULTILINE|re.DOTALL)
    if m : #found something (event "" is OK)
        ret = m.groups()[0]
        logging.debug("Found content")
        main = filter_reply_chars(ret)
    else :
        main = None
    return (main, added)

def filter_reply_chars(text):
    """filter reply characters (>) and strip empty lines"""
    ret = ""
    #FIXME : one regexp and not a loop ?
    for line in text.split("\n") : #clean replychars
        ret = ret + re.sub(r'^[\s>]*', "", line, re.MULTILINE|re.DOTALL) + "\n"
    ret = re.sub(r'\n\s*\n+', "\n", ret, re.MULTILINE|re.DOTALL) #strip double blank
    return(ret.strip())

def extract_uid(text):
    """Extract UID from text (subject of the email)"""
    #FIXME : shall we precompile the regex ?
    ref = r'\sUMR/(.+?@.+?)\s*$' #UID is at least x@x characters
    m = re.search(ref, text)
    if m : #found
        return(m.groups(0)[0])
    else : #not found
        return None

def process_mails():
    """Fetch mails, parse, update store, and send back the event"""
    l = fetchMails() #fetch mails in inbox
    for sender, message in l : #for each sender,message
        logging.debug("Processing mail from %s", sender)
        uid = extract_uid(message['Subject'])
        text, added = extract_content(get_content_as_text(message))
        if uid is None or (text is None and added is None):
            continue #Nothing to do
        if added is not None : #append with added and discard main text
            stored = UmrIcal.get_data_from_store(uid) #get data
            text = stored['meetingplan']
            text += "\n--\n" + added
        data = { #prepare update
            'meetingplan': text,
            'updated': UmrIcal.ts_from_datetime(),
            'uid' : uid
        }
        UmrIcal.update_store_with_data(data) #update in store
        UmrIcal.send_event_from_uid(uid, prefix="PROCESSED") #send from store
    disconnect() #disconnect close the pop connection and mark messages as read.

if __name__ == '__main__':
    print("Test UmrMail")
