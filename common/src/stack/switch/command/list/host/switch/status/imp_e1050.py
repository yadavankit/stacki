# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import json
import re
import stack.commands


class Implementation(stack.commands.Implementation):
	def run(self, args):
		switch = args[0]
		# better to get hosts from switch hostfile? also, 'net show bridge macs <ip>' suggests switch knows host IP
		hosts = self.owner.call('list.host.interface', ['output-format=json'])

		with SwitchCelesticaE1050(switch_address, switch_name, switch_username, switch_password) as switch:
			# better name(s)?
			interfaces = switch.json_loads(cmd="show interface json")

			for iface_obj in sorted(switch.json_loads(cmd="show bridge macs dynamic json"), key=lambda d: d['dev']):  # why did they call iface 'dev'?
				mac = iface_obj['mac']
				port = re.search(r'\d+', iface_obj['dev']).group()
				vlan = iface_obj['vlan']  # should VLAN come from FE or switch? Missing from FE atm
				# TODO: multiple VLANs?

				speed = interfaces[iface_obj['dev']]['speed']
				state = interfaces[iface_obj['dev']]['linkstate']

				for host_obj in hosts:
					if host_obj['mac'] == mac:
						host = host_obj['host']
						interface = host_obj['interface']


						self.owner.addOutput(host, [mac, interface, vlan, switch_name, port, speed, state])
						break
