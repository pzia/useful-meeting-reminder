#!/usr/bin/python3
# -*- coding: utf-8 -*-

#Umr imports
from UmrConf import gconfig
import UmrIcal
import UmrMail

if __name__ == '__main__':
    """Connect, fetch messages, and answer with initial content"""
    events = UmrIcal.get_events_from_store()
    reminded = UmrIcal.remind_events(events)
    print(UmrIcal.print_events(reminded))