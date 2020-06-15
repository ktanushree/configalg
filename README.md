# CloudGenix Disable SIP ALG
This script is used to disable SIP ALG on CloudGenix devices running pre 5.2.1 software release. 

#### Synopsis
This script enables disabling SIP ALG on devices running software releases older than 5.2.1. For 5.2.1 and higher versions, NAT Policy can be used to achieve this functionality.


#### Requirements
* Active CloudGenix Account
* Python >=3.6
* Python modules:
    * CloudGenix Python SDK >= 5.2.1b1 - <https://github.com/CloudGenix/sdk-python>

#### License
MIT

#### Installation:
 - **Github:** Download files to a local directory, manually run `disablealg.py`. 

### Examples of usage:
Disable ALG for an element assigned to a site:
```
./disablealg.py -SN Sitename -EN Elemname
```

Help Text:
```angular2
Tanushree:disablealg tanushreekamath$ ./disablealg.py -h
usage: disablealg.py [-h] [--controller CONTROLLER] [--email EMAIL]
                     [--pass PASS] [--sitename SITENAME] [--elemname ELEMNAME]

CloudGenix: Disable ALG.

optional arguments:
  -h, --help            show this help message and exit

API:
  These options change how this program connects to the API.

  --controller CONTROLLER, -C CONTROLLER
                        Controller URI, ex. C-Prod:
                        https://api.elcapitan.cloudgenix.com

Login:
  These options allow skipping of interactive login

  --email EMAIL, -E EMAIL
                        Use this email as User Name instead of prompting
  --pass PASS, -P PASS  Use this Password instead of prompting

Device Specific information:
  Provide the site and element name where ALG needs to be disabled

  --sitename SITENAME, -SN SITENAME
                        Name of the Site
  --elemname ELEMNAME, -EN ELEMNAME
                        Name of the Element
Tanushree:disablealg tanushreekamath$ 
```

#### Version
| Version | Build | Changes |
| ------- | ----- | ------- |
| **1.0.0** | **b1** | Initial Release. |


#### For more info
 * Get help and additional CloudGenix Documentation at <http://support.cloudgenix.com>
 
