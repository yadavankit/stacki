# Copyright (c) 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
import stack.util
from stack.exception import CommandError, ArgUnique
from stack.switch import SwitchException, SwitchInfiniBand

class command(stack.commands.SwitchArgumentProcessor,
	stack.commands.enable.command,
	stack.commands.HostArgumentProcessor):
	pass

class Command(command):
	"""
	Output the switch configuration file to tftp directory.

	<example cmd='report switch'>
	Outputs data for /tftpboot/pxelunux/upload
	</example>
	"""

	def run(self, params, args):

		if len(args) != 1:
			raise ArgUnique(self, 'switch')

		switch = self.getSwitchNames(args)
		for _switch in self.call('list.host.interface', switch):
			model = self.getHostAttr(_switch['host'], 'switch_model')
			self.runImplementation(model, [_switch])

RollName = "stacki"
