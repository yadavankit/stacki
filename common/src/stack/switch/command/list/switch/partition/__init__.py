# @copyright@
# Copyright (c) 2018 Teradata
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

		if len(params) == 1:
			if len(args) != 1:
				raise ArgRequired(self, 'switch')

		subnet_managers =[]
		for sm in self.call('list.switch.sm'):
			if sm['subnet_manager'] == "enable":
				subnet_managers.append(sm['switch'])

		switches = self.getSwitchNames(args)
		self.beginOutput()
		for switch in self.call('list.host.interface', switches):
			switch_name = switch['host']
			model = self.getHostAttr(switch_name, 'switch_model')
			
			if len(args) == 0 and switch_name not in subnet_managers:
				continue

			self.runImplementation(model, [switch] + [params])

		self.endOutput(header=['switch', 'partition', 'key', 'member', 'host', 'interface'], trimOwner=True)
		#self.endOutput(header=['switch', 'partition', 'key', 'member', 'host', 'interface'])

RollName = "stacki"
