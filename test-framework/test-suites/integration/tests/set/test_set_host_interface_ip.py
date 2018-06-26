import json
import os
import pytest
import subprocess

class TestSetHostInterfaceIp:
	def test_set_host_interface_ip_auto(self, host, set_host_interface):
		"Test if ip=AUTO assigns a valid, unique IP address"
		
		hostname  = set_host_interface['hostname']
		interface = set_host_interface['interface']
		ip_list   = set_host_interface['ip_list']

		op = host.run("stack set host interface ip %s ip=AUTO interface=%s" % \
			(hostname, interface))
		assert op.rc == 0
		
		op = host.run("stack list host interface %s output-format=json" % hostname)
		o = json.loads(op.stdout)
		ip = None

		for line in o:
			if line['interface'] == interface:
				ip = line['ip']

		# Check if no other interface in the same network has this IP.
		assert(ip not in ip_list)
