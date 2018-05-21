# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import re
import stack.commands
from stack.exception import CommandError
from stack.switch import SwitchInfiniBand, SwitchException


class Implementation(stack.commands.Implementation):
	def run(self, args):

		switch = args[0]
		switch_address = switch['ip']
		switch_name = switch['host']
		switch_username = self.owner.getHostAttr(switch_name, 'switch_username')
		switch_password = self.owner.getHostAttr(switch_name, 'switch_password')

		partition = None
		if len(args[1]) == 1:
			partition = args[1]['partition']

		# Check if the switch has an ip address
		if not switch_address:
			raise CommandError(self, '"%s" has no address to connect to.' % switch_name)

		# Connect to the switch
		with SwitchInfiniBand(switch_address, switch_name, switch_username, switch_password) as switch:
			try:
				switch.connect()
				output = switch.show_partition_member(partition)
				for line in output.splitlines():
					if "show ib partition" in str(line) or "members" in str(line):
						continue
					if "b' " not in str(line) and "GUID=" not in str(line):
						continue
					sub_pattern = re.compile("^b'|^b\"|'$|\"$")
					filter_output = re.sub(sub_pattern, "", str(line))
					self.owner.addOutput(switch_name, filter_output)

			except SwitchException as switch_error:
				raise CommandError(self, switch_error)
			except:
				raise CommandError(self, "There was an error getting the partition of the switch.")

RollName = "stacki"
