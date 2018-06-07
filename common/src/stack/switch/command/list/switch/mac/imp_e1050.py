# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import re
import stack.commands
from stack.switch import SwitchCelesticaE1050  #, SwitchException


class Implementation(stack.commands.Implementation):
	def run(self, args):
		switch = args[0]

		switch_name = switch['host']
		switch_address = switch['ip']
		switch_username = self.owner.getHostAttr(switch_name, 'switch_username')
		switch_password = self.owner.getHostAttr(switch_name, 'switch_password')

		with SwitchCelesticaE1050(switch_address, switch_name, switch_username, switch_password) as switch:
			with switch.sorted_json("show interface json") as data:
				for iface in data:
					port_match = re.search(r'\d+', iface)
					info = data[iface]
					if 'swp' in iface and info['linkstate'] != 'DN':
						iface_obj = info['iface_obj']

						port = port_match.group()
						vlan = '' if not iface_obj['vlan'] else iface_obj['vlan'][0]['vlan']  # handle multiple VLANs?

						self.owner.addOutput(switch_name,
						                    [port, iface_obj['mac'], '', iface, vlan])  # host missing, switch hostfile?
