# @copyright@
# Copyright (c) 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
from stack.exception import CommandError, ParamRequired
from stack.switch import SwitchInfiniBand, SwitchException

class command(stack.commands.SwitchArgumentProcessor,
	      stack.commands.add.command):
	pass

class Command(command):
	"""
	Add a partition to subnet managers

	<param type='string' name='partition' optional='0'>
	partition is the partition name
	</param>

	<param type='string' name='key' optional='1'>
	key is the partition key for the partition
	</param>

	<example cmd='add infiniband partition partition=coke key=2'>
	Add partition 'coke' with key '2' to subnet manager(s)
	</example>
	"""


	def run(self, params, args):

		partition, key = self.fillParams([
		              ('partition', None, True),
		              ('key', None, True),
		              ])

		# Get all the IB switches that are subnet managers
		# There must be 1 sm per fabric. If there are more then 1 sm per fabric
		# then disable all except one. If there are no sm then try to enable
		# one sm per fabric

		ib0_sm = None
		ib1_sm = None
		for switch in self.call('list.switch.sm'):
			if switch['subnet_manager']  == "enable":
				switch_name = switch['switch']
				for output in self.call('list.host.interface', [switch_name]):
					if ib0_sm == None and output['interface'] == "ib0":
						# Found ib0 subnet manager
						ib0_sm = switch_name
					elif ib1_sm == None and output['interface'] == "ib1":
						# Found ib1 subnet manager
						ib1_sm = switch_name
					elif ib0_sm != None or ib1_sm != None:
						# Found multiple subnet manager in the same fabric.
						# We need to disable it since we can not have multiple
						# subnet manager in the same fabric
						Log('Disable subnet manager on "%s"' % switch_name)
						try:
							self.call('disable.switch.sm', [switch_name])
						except:
							raise CommandError(self, 'Can not disable subnet manager on "%s"' % switch_name)

		# If there is no subnet manager then enable one from each fabric 
		if ib0_sm == None or ib1_sm == None:
			for switch in self.call('list.switch'):
				switch_name = switch['switch']
				for output in self.call('list.host.interface', [switch_name]):
					if output['interface'] == "ib0" and ib0_sm == None:
						ib0_sm = switch_name
						self.call('enable.switch.sm', [switch_name])
					elif output['interface'] == "ib1" and ib1_sm == None:
						ib1_sm = switch_name
						self.call('enable.switch.sm', [switch_name])

		if ib0_sm == None and ib1_sm == None:
			raise CommandError(self, 'Can not enable subnet manager') 

		# Adding partition information as attributes to sm which will get
		# sync to the switch with the "stack sync infiniband" command
		for sm in [ib0_sm, ib1_sm]:
			self.call('set.host.attr',
				[sm,
				"attr=partition.name.%s" % key,
				"value=%s" % partition
				])

RollName = "stacki"
