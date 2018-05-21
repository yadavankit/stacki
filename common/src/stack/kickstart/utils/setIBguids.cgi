#!/opt/stack/bin/python3
#
# @copyright@
# Copyright (c) 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import os
import cgi
import re
import syslog
import json
import stack.api


def _convert_guid(guid):
	"""
	guid format range 00:00:00:00:00:00:00:00 - ff:ff:ff:ff:ff:ff:ff:ff
	"""
	guid_format = re.compile("([0-9a-fA-F][0-9a-fA-F]:){7}[0-9a-fA-F][0-9a-fA-F]")
	guid_plain = re.compile("([0-9a-fA-F]){16}")
	
	guid = guid.lower()
	guid = guid.replace("0x", "")

	if guid_plain.match(guid):
		new_guid = ""
		for each in range(0, 16, 2):
			new_guid += guid[each:each + 2] + ":"
		guid = new_guid[:-1]
		
	if not guid_format.match(guid):
		return None

	return guid

syslog.openlog('setIBguids.cgi', syslog.LOG_PID, syslog.LOG_LOCAL0)

#
# get the name of the node that is issuing the request
#
ipaddr = None
if 'REMOTE_ADDR' in os.environ:
	ipaddr = os.environ['REMOTE_ADDR']
if not ipaddr:
	sys.exit(-1)
	
syslog.syslog(syslog.LOG_INFO, 'remote addr %s' % ipaddr)

# 'params' field should be a python dictionary of the form:
#
# { 'action': value }
#
# It is json encoded for transport to keep things simple, and
# help us only treat the values as data.

form = cgi.FieldStorage()
params = None
ib0guid = None
ib1guid = None
try:
	params = form['params'].value
	try:
		params = json.loads(params)
		syslog.syslog(syslog.LOG_INFO, 'params %s' % params)
		try:
			ib0guid = params['ib0guid']
			ib1guid = params['ib1guid']
		except:
			syslog.syslog(syslog.LOG_ERR, 'no attribute ib0guid/ib1guid speficied')
	except:
		syslog.syslog(syslog.LOG_ERR, 'invalid params %s' % params)
except:
	syslog.syslog(syslog.LOG_ERR, 'missing params')

ib0guid = _convert_guid(ib0guid
syslog.syslog(syslog.LOG_INFO, 'ib0guid %s' % ib0guid)
ib1guid = _convert_guid(ib1guid)
syslog.syslog(syslog.LOG_INFO, 'ib1guid %s' % ib1guid)

if ib0guid != None:
	stack.api.Call('set host attr', [ ipaddr, 'attr=ib0guid', 'value=%s' % ib0guid ])

if ib1guid != None:
	stack.api.Call('set host attr', [ ipaddr, 'attr=ib1guid', 'value=%s' % ib1guid ])
	
print('Content-type: application/octet-stream')
print('Content-length: %d' % (len('')))
print('')
print('')

syslog.closelog()
