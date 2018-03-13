#!/usr/bin/python3
# -*- coding: utf-8 -*-

#Umr imports
from UmrConf import gconfig
import UmrIcal
import UmrMail

if __name__ == '__main__':
    """Connect, fetch messages, and answer with initial content"""
    l = UmrMail.fetchMails()
    for sender, message in l :
        text = UmrMail.extract_content(UmrMail.get_content_as_text(message))
        uid = UmrMail.extract_uid(UmrMail.get_title(message))
        data = {
            'meetingplan': text,
            'updated': UmrIcal.ts_from_datetime(),
            'uid' : uid
        }
        UmrIcal.update_store_with_data(data)
        UmrIcal.send_event_from_uid(uid)
    UmrMail.disconnect()