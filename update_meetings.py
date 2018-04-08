#!/usr/bin/python3
# -*- coding: utf-8 -*-

#imports UMR
import UmrIcal

if __name__ == '__main__':
    """Read ical, update/create event in store, delete store enries not in ics"""
    UmrIcal.update_store_from_ical()
    
