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
	Remove a partition from a InfiniBand switch

	<param type='string' partition='coke'>
	Remove partition 'coke'
	</param>

	<example cmd='remove switch partition m7800-1-1-1-18 partition=coke'>
	Add partition 'coke' with pkey '0xf' to switch m7800-1-1-1-18
	</example>
	"""

	def run(self, params, args):

		if len(args) != 1:
			raise ArgRequired(self, 'switch')
	
		partition, = self.fillParams([('partition', None, True),])

		switch = self.getSwitchNames(args)
		for _switch in self.call('list.host.interface', switch):
			model = self.getHostAttr(_switch['host'], 'switch_model')
			self.runImplementation(model, [_switch] + [params])

RollName = "stacki"
