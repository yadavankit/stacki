# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import re
import stack.commands
from stack.switch.e1050 import SwitchCelesticaE1050
import subprocess


# similar to 'list switch status'; intentional? reusable?
class Implementation(stack.commands.Implementation):
	def run(self, args):
		switch = args[0]

		# TODO: FE has to see BEs over 10.2.232 network (currently can't)
		if self.owner.pinghosts:
			_host_interfaces = [host for host in self.owner.call('list.host.interface')
					if host['network'] == switch['network']]
			for host in _host_interfaces:
				subprocess.run(['ping', '-c', '1', host['ip']])  # , stdout=subprocess.PIPE

		switch_name = switch['host']
		switch_address = switch['ip']
		switch_username = self.owner.getHostAttr(switch_name, 'switch_username')
		switch_password = self.owner.getHostAttr(switch_name, 'switch_password')

		# better to get hosts from switch hostfile? also, 'net show bridge macs <ip>' suggests switch knows host IP
		hosts = self.owner.call('list.host.interface', ['output-format=json'])

		with SwitchCelesticaE1050(switch_address, switch_name, switch_username, switch_password) as switch:
			# better name(s)?
			for iface_obj in sorted(switch.json_loads(cmd="show bridge macs dynamic json"), key=lambda d: d['dev']):  # why did they call iface 'dev'?
				mac = iface_obj['mac']
				port = re.search(r'\d+', iface_obj['dev']).group()
				vlan = iface_obj['vlan']  # should VLAN come from FE or switch? Missing from FE atm
				# TODO: multiple VLANs?

				for host_obj in hosts:
					if host_obj['mac'] == mac:
						host = host_obj['host']
						interface = host_obj['interface']

						self.owner.addOutput(switch_name, [port, mac, host, interface, vlan])
						break

