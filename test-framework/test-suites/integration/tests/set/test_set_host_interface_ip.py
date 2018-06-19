import json
import os
import subprocess

import pytest


@pytest.mark.usefixtures("add_host")
class TestSetHostInterfaceIp:
	def test_set_host_interface_ip_auto(self, host):
		"Test the output when the discovery daemon is not running"

		# Make sure discovery isn't running
		op = host.run("stack list network private output-format=json")
		o = json.loads(op.stdout)
		addr = o[0]['address']
		mask = o[0]['mask']

		op = host.run("stack list host a:backend output-format=json")
		o = json.loads(op.stdout)
		hostname = o[0]['host']

		op = host.run("stack list host interface output-format=json")
		o = json.loads(op.stdout)
		ip_list = []
		interface = None

		for line in o:
			if line['host'] == hostname:
				interface = line['interface']
			# Make list of IP addresses
			ip_list.append(line['ip'])

		op = host.run("stack set host interface ip %s ip=AUTO interface=%s" % (hostname, interface))
		assert op.rc == 0
		
		op = host.run("stack list host interface %s output-format=json" % hostname)
		o = json.loads(op.stdout)
		ip = None

		for line in o:
			if line['interface'] == interface:
				ip = line['ip']

		# Check if no other interface in the same network has this IP.
		assert(ip not in ip_list)
