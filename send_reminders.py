#!/usr/bin/python3
# -*- coding: utf-8 -*-

#Umr imports
from UmrConf import gconfig
import UmrIcal

if __name__ == '__main__':
    """Connect, fetch messages, and answer with initial content"""
    UmrIcal.send_reminders()