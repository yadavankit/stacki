# @copyright@
# Copyright (c) 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
from stack.exception import CommandError
from stack.switch import SwitchException, SwitchInfiniBand


class Implementation(stack.commands.Implementation):
	def run(self, args):

		switch = args[0]
		switch_address = switch['ip']
		switch_name = switch['host']
		switch_username = self.owner.getHostAttr(switch_name, 'switch_username')
		switch_password = self.owner.getHostAttr(switch_name, 'switch_password')

		param = args[1]
		partition = param['partition']
		members = (param['member']).split(',')

		# Connect to the switch
		with SwitchInfiniBand(switch_address, switch_name, switch_username, switch_password) as _switch:
			try:
				_switch.connect()
				for m in members:
					_switch.add_partition_member(partition, m)
			except SwitchException as switch_error:
				raise CommandError(self, switch_error)
			except Exception as found_error:
				raise CommandError(self, "There was an error adding member to partition")

RollName = "stacki"
