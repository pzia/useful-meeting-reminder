# -*- coding: utf-8 -*-

#config
import configparser

#sys & os
import sys
import os.path

#set logging
import logging
logging.basicConfig(filename=os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'umr.log'),level=logging.DEBUG)

#Set locale
#FIXME : force French, should be in conf ?
import locale
locale.setlocale(locale.LC_TIME, 'fr_FR')

#Initialisation to None
gconfig = None

#config helpers
def localpath():
    """Path of launcher, supposed to be the root of the tree"""
    return(os.path.dirname(os.path.abspath(sys.argv[0])))

def get_config(cname = 'umr.ini'):
    """Load config as a dict"""
    #Configuration
    global gconfig
    if gconfig == None :
        logging.info("Load config")
        gconfig = configparser.ConfigParser()
        gconfig.readfp(open(os.path.join(localpath(), cname)))
        #logging.info("Config loaded, user %s" % gconfig.get('User', 'login'))
    return gconfig

def get_path(pathname_config, filename_config = None):
    """Helper to get pathname from config, and create if necessary"""
    #check path
    conf_path = os.path.join(localpath(), gconfig.get('Path', pathname_config))
    if not os.path.exists(conf_path) :
        logging.debug("Creating %s", conf_path)
        os.mkdir(conf_path)
    if filename_config is not None:
        filename = gconfig.get("Files", filename_config)
        conf_path = os.path.join(conf_path, filename)
    return(conf_path)

gconfig = get_config()
