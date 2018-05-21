# @copyright@
# Copyright (c) 2018 Teradata
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
	Add a guid/member to a Infiniband switch partition

	<param type='string' name='partition' optional='0'>
	Partition name in the switch
	</param>
	
	<param type='string' name='member' optional='1'>
	Member/guid to add to the partition
	</param>

	<example cmd='add switch partition member m7800-1-1-1-18 partition=coke member=00:11:22:33:44:55:66:77'>
	Add member 00:11:22:33:44:55:66:77 to partition 'coke' in switch m7800-1-1-1-18
	</example>
	"""

	def run(self, params, args):

		if len(args) != 1:
			raise ArgRequired(self, 'switch')
		
		partition, member = self.fillParams([
		              ('partition', None, True),
		              ('member', None, True),
		              ])

		switch = self.getSwitchNames(args)
		for _switch in self.call('list.host.interface', switch):
			model = self.getHostAttr(_switch['host'], 'switch_model')
			self.runImplementation(model, [_switch] + [params])

RollName = "stacki"
