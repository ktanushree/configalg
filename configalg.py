#!/usr/bin/env python
"""
CGNX script to enable or disable SIP ALG

tanushree@cloudgenix.com

"""
import cloudgenix
import pandas as pd
import os
import sys
import yaml
from netaddr import IPAddress, IPNetwork
from random import *
import argparse
import logging


# Global Vars
SDK_VERSION = cloudgenix.version
SCRIPT_NAME = 'CloudGenix: Disable ALG'


# Set NON-SYSLOG logging to use function name
logger = logging.getLogger(__name__)

try:
    from cloudgenix_settings import CLOUDGENIX_AUTH_TOKEN

except ImportError:
    # will get caught below.
    # Get AUTH_TOKEN/X_AUTH_TOKEN from env variable, if it exists. X_AUTH_TOKEN takes priority.
    if "X_AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('X_AUTH_TOKEN')
    elif "AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
    else:
        # not set
        CLOUDGENIX_AUTH_TOKEN = None

try:
    from cloudgenix_settings import CLOUDGENIX_USER, CLOUDGENIX_PASSWORD

except ImportError:
    # will get caught below
    CLOUDGENIX_USER = None
    CLOUDGENIX_PASSWORD = None


siteid_sitename_dict = {}
sitename_siteid_dict = {}
elemname_elemid_dict = {}
elemname_sitename_dict = {}

actionxlate = {"DISABLE": False, "ENABLE": True}

def createdicts(cgx_session):
    resp = cgx_session.get.sites()
    if resp.cgx_status:
        sitelist = resp.cgx_content.get("items",None)
        for site in sitelist:
            sid = site['id']
            sname = site['name']
            siteid_sitename_dict[sid] = sname
            sitename_siteid_dict[sname] = sid
    else:
        print("ERR: Could not retrieve sites")
        cloudgenix.jd_detailed(resp)

    resp = cgx_session.get.elements()
    if resp.cgx_status:
        elemlist = resp.cgx_content.get("items",None)
        for elem in elemlist:
            eid = elem['id']
            ename = elem['name']
            sid = elem['site_id']
            elemname_elemid_dict[ename] = eid
            if sid == "1":
                continue

            sname = siteid_sitename_dict[sid]
            elemname_sitename_dict[ename] = sname

    else:
        print("ERR: Could not retrieve sites")
        cloudgenix.jd_detailed(resp)

    return


def go():
    ############################################################################
    # Begin Script, parse arguments.
    ############################################################################

    # Parse arguments
    parser = argparse.ArgumentParser(description="{0}.".format(SCRIPT_NAME))

    # Allow Controller modification and debug level sets.
    controller_group = parser.add_argument_group('API', 'These options change how this program connects to the API.')
    controller_group.add_argument("--controller", "-C",
                                  help="Controller URI, ex. "
                                       "C-Prod: https://api.elcapitan.cloudgenix.com",
                                  default="https://api.elcapitan.cloudgenix.com")

    login_group = parser.add_argument_group('Login', 'These options allow skipping of interactive login')
    login_group.add_argument("--email", "-E", help="Use this email as User Name instead of prompting",
                             default=None)
    login_group.add_argument("--pass", "-P", help="Use this Password instead of prompting",
                             default=None)

    # Commandline for entering Site info
    site_group = parser.add_argument_group('Device Specific information',
                                           'Provide the site and element name where ALG needs to be disabled')
    site_group.add_argument("--sitename", "-SN", help="Name of the Site", default=None)
    site_group.add_argument("--elemname", "-EN", help="Name of the Element", default=None)
    site_group.add_argument("--action", "-A", help="Action for ALG configuration. Select ENABLE or DISABLE", default=None)


    args = vars(parser.parse_args())

    ############################################################################
    # Extract Command Line Arguments
    ############################################################################
    sitename = args['sitename']
    elemname = args['elemname']
    action = args['action']

    if (sitename is None) or (elemname is None):
        print("ERR: Please provide both Site and Element names")
        sys.exit()

    if action not in ["ENABLE", "DISABLE"]:
        print("ERR: Incorrect action: {}. Please select ENABLE or DISABLE".format(action))
        sys.exit()

    ############################################################################
    # Instantiate API & Login
    ############################################################################

    cgx_session = cloudgenix.API(controller=args["controller"], ssl_verify=False)
    print("{0} v{1} ({2})\n".format(SCRIPT_NAME, SDK_VERSION, cgx_session.controller))

    # login logic. Use cmdline if set, use AUTH_TOKEN next, finally user/pass from config file, then prompt.
    # figure out user
    if args["email"]:
        user_email = args["email"]
    elif CLOUDGENIX_USER:
        user_email = CLOUDGENIX_USER
    else:
        user_email = None

    # figure out password
    if args["pass"]:
        user_password = args["pass"]
    elif CLOUDGENIX_PASSWORD:
        user_password = CLOUDGENIX_PASSWORD
    else:
        user_password = None

    # check for token
    if CLOUDGENIX_AUTH_TOKEN and not args["email"] and not args["pass"]:
        cgx_session.interactive.use_token(CLOUDGENIX_AUTH_TOKEN)
        if cgx_session.tenant_id is None:
            print("AUTH_TOKEN login failure, please check token.")
            sys.exit()

    else:
        while cgx_session.tenant_id is None:
            cgx_session.interactive.login(user_email, user_password)
            # clear after one failed login, force relogin.
            if not cgx_session.tenant_id:
                user_email = None
                user_password = None

    ############################################################################
    # Validate Site & Element Name and Config SIP ALG
    ############################################################################
    createdicts(cgx_session)
    if sitename in sitename_siteid_dict.keys():
        sid = sitename_siteid_dict[sitename]

        if elemname in elemname_sitename_dict.keys():
            sname = elemname_sitename_dict[elemname]

            if sname == sitename:
                eid = elemname_elemid_dict[elemname]

                print("INFO: Element {} found attached to site {}".format(elemname, sitename))

                resp = cgx_session.get.element_extensions(site_id=sid, element_id=eid)
                if resp.cgx_status:
                    extensions = resp.cgx_content.get("items",None)
                    extfound = False
                    for ext in extensions:
                        if ext['namespace'] == "algconfig":
                            print("INFO: ALG Config on {}:{}".format(sitename,elemname))
                            extfound = True

                            conf = {
                                "rules":[
                                    {
                                        "alg": "SIP",
                                        "enabled": actionxlate[action]
                                    }
                                ]
                            }

                            ext["conf"] = conf

                            resp = cgx_session.put.element_extensions(site_id=sid, element_id=eid, extension_id=ext['id'],data=ext)
                            if resp.cgx_status:
                                print("INFO: SIP ALG {}D on {}:{}".format(action,sitename,elemname))
                            else:
                                print("ERR: Could not edit ALG config on {}:{}\n{}".format(sitename,elemname,cloudgenix.jd_detailed(resp)))

                    if not extfound:
                        print("INFO: No ALG Config on {}:{}".format(sitename,elemname))

                        data = {
                            "name" : "alg",
                            "namespace":"algconfig",
                            "entity_id": None,
                            "conf":{
                                "rules":[
                                    {
                                        "alg": "SIP",
                                        "enabled": actionxlate[action]
                                     }
                                ]
                            },
                            "disabled":False,
                        }

                        print("Using element extensions API to configure: {}".format(data))
                        resp = cgx_session.post.element_extensions(site_id=sid, element_id=eid, data=data)
                        if resp.cgx_status:
                            print("INFO: SIP ALG {}D on {}:{}".format(action,sitename, elemname))

                        else:
                            print("ERR: Could not {} SIP ALG.\n {}".format(action, cloudgenix.jd_detailed(resp)))

            else:
                print("ERR: Element {} is not attached to site {}. Please reenter site name and element name".format(elemname,sitename))

        else:
            print("ERR: Element {} not found. Please reenter element name".format(elemname))

    else:
        print("ERR: Site {} not found. Please reenter site name".format(sitename))

    ############################################################################
    # Logout to clear session.
    ############################################################################
    cgx_session.get.logout()

    print("INFO: Logging Out")
    sys.exit()

if __name__ == "__main__":
    go()
