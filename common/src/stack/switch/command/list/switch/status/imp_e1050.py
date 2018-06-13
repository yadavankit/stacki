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

		switch_name = switch['host']
		switch_address = switch['ip']
		switch_username = self.owner.getHostAttr(switch_name, 'switch_username')
		switch_password = self.owner.getHostAttr(switch_name, 'switch_password')
''' derp
		# better to get hosts from switch hostfile? also, 'net show bridge macs <ip>' suggests switch knows host ip
		hosts = self.owner.call('list.host.interface', ['output-format=json'])
		with SwitchCelesticaE1050(switch_address, switch_name, switch_username, switch_password) as switch:
			bm_iface_objs = {}
			for bm_iface_obj in switch.json_loads(cmd="show bridge macs dynamic json"):
				iface = bm_iface_obj.pop('dev')  # why did they call iface 'dev'?
				bm_iface_objs[iface] = bm_iface_obj

			ifaces = switch.json_loads(cmd="show interface json")  # better name?

			for iface in switch.sorted_keys(ifaces):
				if 'swp' in iface:
					if_iface_obj = ifaces[iface]['iface_obj']

					try:
						bm_iface_obj = bm_iface_objs[iface]
						mac = bm_iface_obj['mac']

						for host_obj in hosts:
							if host_obj['mac'] == mac:
								host = host_obj['host']
								interface = host_obj['interface']
								break
					except KeyError:
						host = ''
						interface = ''
						mac = ''

					port = re.search(r'\d+', iface).group()
					speed = if_iface_obj['speed']
					state = if_iface_obj['linkstate']
					vlan = bm_iface_obj['vlan']  # should vlan come from FE or switch? Missing from FE atm

					self.owner.addOutput(switch_name, [port, speed, state, mac, vlan, host, interface])
'''

''' old; current doesn't show inactive ports
with SwitchCelesticaE1050(switch_address, switch_name, switch_username, switch_password) as switch:
	data = switch.json_loads("show interface json")
	for iface in switch.sorted_keys(data):
		port_match = re.search(r'\d+', iface)
		info = data[iface]
		if 'swp' in iface:
			iface_obj = info['iface_obj']

			port = port_match.group()
			# mac and interface are for host, but are stored in switch; figure out where
			# should vlan come from FE or switch?
			vlan = '' if not iface_obj['vlan'] else iface_obj['vlan'][0]['vlan']  # handle multiple VLANs?

			self.owner.addOutput(switch_name, [port, info['speed'], info['linkstate'], iface_obj['mac'], vlan, '', iface])  # host missing, switch hostfile?
'''
