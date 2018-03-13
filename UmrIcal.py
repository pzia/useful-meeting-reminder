#!/usr/bin/python3
# -*- coding: utf-8 -*-

#imports UMR
from UmrConf import gconfig
import UmrConf
import UmrMail

#system & debug
import os.path
import logging

#date manipulation
from datetime import datetime, timezone, timedelta
from dateutil import rrule
from icalendar import Calendar, parser_tools, Event, vDatetime

#misc
import hashlib, json

def get_events(pathname, maxfuture = 60, limit = 200):
    """Read ics file and get <limit> events for the <maxfuture> days"""
    assert type(pathname)==str
    assert type(maxfuture)==int
    assert type(limit)==int

    logging.info("Getting max %d future events from %s in less than %d", limit, pathname, maxfuture)
    #time limit
    futuredate = datetime.now(timezone.utc)+timedelta(days=maxfuture)
    now = datetime.now(timezone.utc)+timedelta(days=0)
    oldestdate = datetime.now(timezone.utc)+timedelta(days=-maxfuture)

    #open calendar
    g = open(pathname,'rb')
    logging.debug("Import %s events", pathname)
    gcal = Calendar.from_ical(g.read())
    listevents = [] #for events to return

    for component in gcal.walk(): #for each event
        if limit == 0 :
            break #enough !
        if component.name == "VEVENT": #OK, this is a meeting
            dtstart = component.get('dtstart') #start of event

            dt = dtstart.dt.replace(tzinfo=timezone.utc)
            if component.has_key('rrule'): #event with repeat
                rule = component.get('rrule')
                until = rule['UNTIL'][0]
                ruleset = rrule.rruleset()
                ruleset.rrule(rrule.rrulestr(rule.to_ical().decode('UTF-8'), dtstart=dtstart.dt))
                exdate = component.get('EXDATE')
                if exdate is not None :
                    for edate in exdate :
                        ruleset.exdate(edate.dts[0].dt)
                target = None
                for devent in ruleset:
                    if devent > now and (target is None or devent < target):
                        target = devent
                if target is not None :
                    del(component['dtstart'])
                    component.add('dtstart', target)#] = vDatetime(target).to_ical()
                    listevents.append(component) #old, but repeat recently
                    logging.debug("Keeping %s, %s", until, component.get('summary'))
                    limit -= 1 #one more
            elif dt > oldestdate and dt < futuredate:
                    listevents.append(component)
                    logging.debug("Keeping %s, %s", dt, component.get('summary'))
                    limit -= 1

    g.close()
    return(listevents)

def body_event_from_data(data):
    """Make event body from dict"""
    #FIXME : eventually, do it in html
    assert 'dtstart' in data
    assert 'summary' in data
    assert 'description' in data
    #assert 'meetingplan' in data

    bodylist = ["%s" % datetime.utcfromtimestamp(int(data['dtstart'])).strftime('%d-%m-%Y à %H:%M'), data['summary']]
    if 'location' in data and data['location'] != "" :
        bodylist.append(data['location'])
    bodylist.append(body_plan_from_data(data))

    body = "\n".join(bodylist)
    return(body)

def body_plan_from_data(data) :
    """Make plan text from data"""
    plan = "" #FIXME : Default plan ?
    if "meetingplan" in data and data['meetingplan'] != "" :
        plan = data['meetingplan']
    elif 'description' in data and data['description'] != "" :
        plan = data['description']
    return("===\n%s\n===\n" % plan)

def subject_from_data(data):
    """Make Title from dict"""
    dtiso = datetime.utcfromtimestamp(int(data['dtstart'])).strftime('%d-%m-%Y à %H:%M')
    #FIXME : eventually, take it from config file
    return("[UMR] %s - %s - UMR/%s" % (data['summary'], dtiso, data['uid']) )

def send_event_from_uid(uid, prefix = None):
    """Send mail for uid with data from store"""
    #FIXME : Should connect once for all events
    data = get_data_from_store(uid) #get data
    logging.debug("Send event for %s" % uid)
    subject = subject_from_data(data) #subject
    text = body_event_from_data(data)
    if prefix is not None :
        text = "%s\n%s" % (prefix, text)
    #Send
    UmrMail.sendOneMail([gconfig.get('Mail', 'reminded')], subject, text)

def ts_from_datetime(dt = None) :
    if dt == None :
        dt = datetime.now()
    return(int(dt.replace(tzinfo=timezone.utc).timestamp()))

def make_data_from_event(event):
    """Make data dict from ics event"""
    ret = {}
    ret['summary'] = event.get('summary').strip()
    ret['location'] = event.get('location').strip()
    ret['description'] = event.get('description').strip()
    ret['uid'] = event.get('uid')
    ret['dtstart'] = ts_from_datetime(event.get('dtstart').dt)
    #FIXME : Duration ?
    #ret['dtend'] = get_epoc_from_datetime(component.get('dtend').dt)
    return(ret)

def get_data_from_store(uid):
    """Read data from store with uid"""
    fpath = get_store_pathname(uid)
    if os.path.exists(fpath) : #already known
        return(get_data_from_file(fpath))
    else :
        return({})

def get_data_from_file(fpath):
    """Read json file"""
    with open(fpath, 'r') as h : 
        data = json.load(h) #load existing datas
        data['read'] = datetime.now().timestamp()
        logging.debug("Existing datas for uid %s loaded from %s", data['uid'], fpath)
        return(data)

def get_store_pathname(uid):
    """Build meeting store pathname (uid md5 hash)"""
    return(os.path.join(UmrConf.get_path('store'), hashlib.md5(uid.encode()).hexdigest()+".json"))

def write_store_with_data(data):
    """Write meeting store entry from data dict"""
    assert 'dtstart' in data
    assert 'uid' in data
    fpath = get_store_pathname(data['uid'])
    data['written'] = datetime.now().timestamp()
    with open(fpath, 'w') as h:
        json.dump(data, h, indent=2)
        logging.debug("Writing %s for uid %s", fpath, data['uid'])
    return(data)

def update_store_with_data(data):
    """Update meeting store entry from data dict"""
    logging.info("Updating store for uid %s", data['uid'])
    ret = get_data_from_store(data['uid'])
    ret.update(data) #replace existing data
    ret = write_store_with_data(ret)
    return(ret)

def update_store_from_event(event):
    """Update meeting store from icalendar event component"""
    return(update_store_with_data(make_data_from_event(event)))

def update_store_from_ical():
    """Update meeting store from ical source"""
    icspath = gconfig.get('Ical', 'path')
    logging.debug("Update meeting store from %s", icspath)
    levents = get_events(icspath, 90) #get events #FIXME : Conf ?
    counter = 0
    uidlist = []
    for e in levents :
        update_store_from_event(e)
        uidlist.append(e.get('uid'))
        counter += 1
    for uid in get_events_from_store():
        if uid not in uidlist :
            remove_event_from_store(uid)

    logging.info("%d events read and created/updated", counter)
    return(counter)

def get_events_from_store():
    """Read events from store"""
    storepath = UmrConf.get_path('store')
    events = {}
    for f in os.listdir(storepath):
        fpath = os.path.join(storepath, f)
        if os.path.isfile(fpath):
            data = get_data_from_file(fpath)
            #Do not filter here
            events[data['uid']] = data
    return(events)

def remove_event_from_store(uid):
    fpath = get_store_pathname(uid)
    try:
        send_event_from_uid(uid, "REMOVED")
        os.remove(fpath)
        logging.debug("%s removed", uid)
    except :
        pass

def remind_event_from_store(uid):
    """Remind event - and update data store"""
    send_event_from_uid(uid, 'REMINDER')
    data = {'reminded' : ts_from_datetime(), 'uid' : uid}
    return(update_store_with_data(data))

def to_be_reminded(data):
    """check if event has to be reminded"""
    assert 'dtstart' in data

    if 'updated' in data :
        updated = data['updated']
    else :
        updated = 0
    if 'reminded' in data :
        reminded = data['reminded']
    else :
        reminded = 0
    halfway = float(max(updated, reminded) + data['dtstart'])/2.0
    now = ts_from_datetime()
    return(now > halfway and now < data['dtstart'])

def to_be_removed(data, oldest = 7):
    """Check if event has to be removed"""
    if 'dtstart' not in data :
        return True
    old = ts_from_datetime()-oldest*24*3600
    return(data['dtstart'] < old)

def purge_events(events):
    """Purge events if necessary"""
    logging.info("Purge events")
    purged = []

    for uid in events :
        data = events[uid]
        if to_be_removed(data):
            remove_event_from_store(uid)
            purged.append(data)
    return(purged)

def remind_events(events):
    """Remind events if necessary"""
    logging.info('Remind events')
    reminded = []

    for uid in events :
        data = events[uid]
        if to_be_reminded(data):
            remind_event_from_store(uid)
            reminded.append(data)
    return(reminded)

def print_events(events):
    for e in events :
        print(json.dumps(e, indent=2))

if __name__ == '__main__':
    print("Test UmrIcal")
    #update_store_from_ical()
    
