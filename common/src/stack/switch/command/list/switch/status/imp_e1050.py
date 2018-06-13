# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import re
import stack.commands
from stack.switch.e1050 import SwitchCelesticaE1050


# similar to 'list switch mac'; intentional? reusable?
class Implementation(stack.commands.Implementation):
	def run(self, args):
		switch = args[0]

		switch_name = switch['host']
		switch_address = switch['ip']
		switch_username = self.owner.getHostAttr(switch_name, 'switch_username')
		switch_password = self.owner.getHostAttr(switch_name, 'switch_password')

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

