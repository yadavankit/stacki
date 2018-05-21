# @copyright@
# Copyright (c) 2006 - 2017 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
import stack.util
from stack.exception import ArgUnique, CommandError, ArgRequired, ParamRequired
from stack.switch import SwitchInfiniBand, SwitchException


class command(stack.commands.SwitchArgumentProcessor,
	      stack.commands.list.command):
	pass

class Command(command):
	"""
	"""
	def run(self, params, args):

		if len(args) != 1:
			raise ArgRequired(self, 'switch')

		if len(params) != 1:
			raise ParamRequired(self, 'partition')

		_switches = self.getSwitchNames(args)
		self.beginOutput()
		for switch in self.call('list.host.interface', _switches):
			switch_name = switch['host']
			model = self.getHostAttr(switch_name, 'switch_model')
			self.runImplementation(model, [switch] + [params])

		self.endOutput(header=['switch'], trimOwner=True)

RollName = "stacki"
