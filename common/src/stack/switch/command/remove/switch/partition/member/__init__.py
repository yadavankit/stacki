# @copyright@
# Copyright (c) 2006 - 2017 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
from stack.exception import ArgUnique, CommandError, ArgRequired, ParamRequired
from stack.switch import SwitchInfiniBand, SwitchException

class command(stack.commands.SwitchArgumentProcessor,
	      stack.commands.remove.command):
	pass

class Command(command):
	"""
	Add a partition to a InfiniBand switch

	<param type='string' name='port' optional='0'>
	Port the host is connected to the switch on
	</param>

	<param type='string' name='interface' optional='1'>
	Name of the interface you want to use to connect to the switch.
	Default: The first interface that is found that shares the
	same network as the switch.
	</param>

	<example cmd='add switch partition m7800-1-1-1-18 pname=coke pkey=0xf'>
	Add partition 'coke' with pkey '0xf' to switch m7800-1-1-1-18
	</example>
	"""

	def run(self, params, args):

		if len(args) != 1:
			raise ArgRequired(self, 'switch')
		
		if len(params) != 2 :
			raise ParamRequired(self, 'pname and member')

		switch = self.getSwitchNames(args)
		for _switch in self.call('list.host.interface', switch):
			model = self.getHostAttr(_switch['host'], 'switch_model')
			self.runImplementation(model, [_switch] + [params])

RollName = "stacki"
