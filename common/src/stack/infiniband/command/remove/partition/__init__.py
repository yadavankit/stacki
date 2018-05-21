# @copyright@
# Copyright (c) 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
from stack.exception import CommandError, ParamRequired
from stack.switch import SwitchInfiniBand, SwitchException

class command(stack.commands.SwitchArgumentProcessor,
	      stack.commands.remove.command):
	pass

class Command(command):
	"""
	Remove a partition from InfiniBand switches which are subnet manager

	<param type='string' name='partition' optional='0'>
	partition is the partition to remove from all subnet managers
	</param>

	<example cmd='remove infiniband partition partition=coke'>
	Remove partition 'coke' from all subnet managers
	</example>
	"""


	def run(self, params, args):

		partition, = self.fillParams([('partition', None, True),])

		subnet_managers = []
		for switch in self.call('list.switch.sm'):
			if switch['subnet_manager']  == "enable":
				subnet_managers.append(switch['switch'])

		if len(subnet_managers) == 0:
			raise CommandError(self, 'Can not find subnet manager(s)')

		for sm in subnet_managers:
			try:
				self.call('remove.switch.partition', [sm, "partition=%s" % partition])
				# Remove the partition attribute from the sm
				for row in self.call('list.host.attr', [sm, "attr=partition.name*"]):
					if row['value'] in partition:
						attr = row['attr']
						self.call('remove.host.attr', [sm, "attr=%s" % attr])

			except:
				raise CommandError(self, 'Can not remove partition "%s"' % partition )

RollName = "stacki"
