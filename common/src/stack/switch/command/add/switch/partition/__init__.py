# @copyright@
# Copyright (c) 2006 - 2017 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
from stack.exception import ArgUnique, CommandError, ArgRequired, ParamRequired
from stack.switch import SwitchInfiniBand, SwitchException

class command(stack.commands.SwitchArgumentProcessor,
	      stack.commands.add.command):
	pass

class Command(command):
	"""
	Add a partition to a InfiniBand switch

	<param type='string' name='partition' optional='0'>
	partition is the partition name
	</param>

	<param type='string' name='key' optional='1'>
	key is the partition key for the partition
	</param>

	<example cmd='add switch partition m7800-1-1-1-18 partition=coke key=0xf'>
	Add partition 'coke' with key '0xf' to switch m7800-1-1-1-18
	</example>
	"""

	def run(self, params, args):

		if len(args) != 1:
			raise ArgRequired(self, 'switch')

		partition, key = self.fillParams([
		              ('partition', None, True),
		              ('key', None, True),
		              ])

		switch = self.getSwitchNames(args)
		for _switch in self.call('list.host.interface', switch):
			model = self.getHostAttr(_switch['host'], 'switch_model')
			self.runImplementation(model, [_switch] + [params])

RollName = "stacki"
