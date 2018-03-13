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
import html2text
#sys
import logging
import sys

COMMASPACE = ", "
cpop = None
csmtp = None

def connectPop():
    """Connect to pop server and return connection handler"""
    global cpop
    if cpop != None : #already connected ?
        return(cpop)
    logging.info("Connecting")
    serverssl = gconfig.get("Mail", 'serverssl')
    portssl = int(gconfig.get("Mail", 'portssl'))
    username = gconfig.get("Mail", 'username')
    password = gconfig.get("Mail", 'password')
    logging.debug("Connecting to %s:%d with user %s", serverssl, portssl, username)

    cpop = poplib.POP3_SSL(serverssl,portssl)
    cpop.user(username)
    cpop.pass_(password)
    #FIXME : test something ?
    return(cpop)

def connectSmtp():
    global csmtp
    if csmtp != None:
        return(csmtp)
    #on se connecte au serveur pour envoyer tout ça
    serversmtp = gconfig.get("Mail", 'serversmtp')
    portsmtp = gconfig.getint("Mail", 'portsmtp')
    username = gconfig.get("Mail", 'username')
    password = gconfig.get("Mail", 'password')

    logging.debug("Connecting to SMTP %s:%d with user %s", serversmtp, portsmtp, username)
    csmtp = smtplib.SMTP_SSL(serversmtp, portsmtp)
    csmtp.login(username, password) #c'est moi !
    return(csmtp)

def fetchMails():
    cpop = connectPop() #connect if not connected
    nb = cpop.stat()[0]
    nb = int(nb) #contient donc le nombre de messages en cours
    logging.debug("%s messages found", nb)
    resultats = []
    if nb > 0 :
        #on parcourt les messages
        for i in range(1, nb+1):
            mp = email.parser.BytesFeedParser(policy=email.policy.default)
            for j in cpop.retr(i)[1]:
                mp.feed(j+b'\r\n')
            fullmail = mp.close()
           
            #notre message : un expéditeur, un contenu
            if 'Reply-To' in fullmail:
                sender = fullmail['Reply-To']
            else :
                sender = fullmail['From']
            message = (sender, fullmail)
            #on ajoute le message à la liste
            resultats.append(message)
    return resultats #on retourne les résultats

def disconnect():
    """Disconnect"""
    cpop = connectPop()
    csmtp = connectSmtp()
    cpop.quit() #close connection, mark messages as read
    csmtp.close()

def makeMimeText(send_to, subject, text):
    """Fabrique un objet email MIME"""
    
    #arrête le programme si les arguments ne sont pas du type attendu
    assert type(send_to)==list
    
    #on crée l'objet message texte
    textmsg = email.mime.text.MIMEText(text, _charset='utf-8')        

    #on fixe les entêtes du message
    textmsg['To'] = COMMASPACE.join(send_to)
    textmsg['Date'] = email.utils.formatdate(localtime=True)
    textmsg['Subject'] = subject

    return(textmsg)

def sendOneMail(send_to, subject, text, files=[]):
        """Envoi un mail"""
        #fabrique le message
        logging.info("Make mail with subject: %s", subject) 
        msg = makeMimeText(send_to, subject, text)
        #envoi
        sendSomeMails([msg])

def sendSomeMails(mailList):
    """Send some messages from message list"""
    logging.info("Sending mails")
    csmtp = connectSmtp()
    sender = gconfig.get("Mail", 'sender')
    sendername = gconfig.get("Mail", 'sendername')
    fromtext = "%s <%s>" % (sendername, sender)
    #on envoie !
    for msg in mailList:
        logging.info("Envoi d'un message à %s", msg['To'])
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
    return(text.strip())

def get_title(emailmessage):
    """Get title (subject) from email"""
    #FIXME : Useless ?
    return(emailmessage['Subject'])

def extract_content(text):
    """Extract useful content"""
    #FIXME : === could be in conf ?
    #TODO : extract additions ? (+++)
    m = re.search(r'===(.*)===', text, re.MULTILINE|re.DOTALL)
    if m : #found something
        ret = m.groups()[0]
        return(filter_reply_chars(ret))
    else :
        return("")

def filter_reply_chars(text):
    """filter reply characters (>) and strip empty lines"""
    ret = ""
    for line in text.split("\n") : #clean replychars
        ret = ret + re.sub(r'^[\s>]*', "", line, re.MULTILINE|re.DOTALL) + "\n"
    ret = re.sub(r'\n\s*\n+', "\n", ret, re.MULTILINE|re.DOTALL) #strip double blank
    return(ret.strip())

def extract_uid(text):
    """Extract UID from text"""
    ref = r'\sUMR/(.+?@.+?)\s*$'
    m = re.search(ref, text)
    if m :
        return(m.groups(0)[0])
    else :
        return None

if __name__ == '__main__':
    print("Test UmrMail")
    """Connect, fetch messages, and answer with initial content"""
    l = fetchMails()
    for sender, message in l :
        text = extract_content(get_content_as_text(message))
        uid = extract_uid(get_title(message))
        data = {
            'meetingplan': text,
            'updated': UmrIcal.ts_from_datetime(),
            'uid' : uid
        }
        UmrIcal.update_store_with_data(data)
        UmrIcal.send_event_from_uid(uid)
