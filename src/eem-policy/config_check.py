::cisco::eem::event_register_syslog pattern "CONFIG_I" maxrun 60
# this is an example of an EEM policy trigger
# based of Joe Clarke version
# https://github.com/CiscoDevNet/python_code_samples_network/blob/master/eem_configdiff_to_spark/sl_config_diff_to_spark.py
# think there is a permissions isssue in ios.  need to create directory in IOs, but then cannot update it with git
# need to copy the script to flash:
'''
!need to have the following config in IOS
event manager directory user policy flash:
event manager directory user policy flash:gs_script/src/eem-policy

do guestshell run bootflash:gs_script/utils/update_git.sh

do copy flash:gs_script/src/eem-policy/config_check.py flash:

Y
no event manager policy config_check.py
event manager policy config_check.py
'''

import eem
import os
import sys
from cli import cli
import re
sys.path.append("/flash/gs_script/src")
from utils.spark_utils import getRoomId, postMessage

# cli version
BACKUP = "flash:run.last"
# python version
PY_BACKUP = "/flash/run.last"

def logSpark(message):
    sparktoken = os.environ.get("SPARKTOKEN")
    if sparktoken is not None:
        roomId = getRoomId("Sanity", sparktoken)
        postMessage(message, roomId, sparktoken)

def sanity():
    '''
    Sanity check to see if device is working properly.   quick check of an IP Address, but could be much more
    :return:
    '''
    # will return the following if shutdown managment IP address
    # '\n% VRF Mgmt-vrf does not have a usable source address\n'
    # result = cli('ping vrf Mgmt-vrf ip 10.10.10.100')
    result = cli('ping 1.1.1.1')
    eem.action_syslog('Sanity' + result, priority=3)
    return False if '0/5' in result else True

def create_backup():
    result = cli('copy run {bak}'.format(bak=BACKUP))
    if not "copied " in result:
        raise IOError('Cannot create backup {}'.format(BACKUP))

def get_diff():
    # first time  there will be no backup to compare to
    if os.path.exists(PY_BACKUP):
        diffs = cli('show archive config diff {bak} system:running-config'.format(bak=BACKUP))
        if 'No changes were found' in diffs:
            eem.action_syslog('No changes',priority=5)
            return
        diff_lines = re.split(r'\r?\n', diffs)
        msg = 'Configuration differences between the running config and last backup:\n'
        msg += '``` {} \n```'.format('\n'.join(diff_lines[:-1]))
        logSpark(msg)
    create_backup()


def main():
    #eem.action_syslog("config changed")
    #logSpark('config changed')
    if not sanity() and os.path.exists(PY_BACKUP):
        result = cli('configure replace {bak} force'.format(bak=BACKUP))
        eem.action_syslog(result, priority=3)
        sys.exit(0)
    try:
        get_diff()
    except IOError as e:
        eem.action_syslog(e, priority=3)

if __name__ == "__main__":
    main()