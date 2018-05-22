# @copyright@
# Copyright (c) 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
import stack.util
import stack.switch
import subprocess
from stack.exception import CommandError

class command(stack.commands.SwitchArgumentProcessor,
	stack.commands.sync.command):
		pass

class Command(command):
	"""
	Add hosts' guid to Infiniband subnet managers

	<example cmd="sync infiniband">
	</example>
	"""

	def run(self, params, args):

		pdic = dict()
		ib0_sm = None
		ib1_sm = None
	
		subnet_managers = []
		for sm in self.call('list.switch.sm'):
			if sm['subnet_manager'] == "enable":
				subnet_managers.append(sm['switch'])
		
		if not len(subnet_managers):
			raise CommandError(self, 'Can not find subnet managers')
		
		if len(subnet_managers) > 2:
			raise CommandError(self, 'There are more than 2 subnet manager')

		for sm in subnet_managers:
			for row in self.call('list.host.interface', [sm]):
				if "ib0" in row['interface']:
					ib0_sm = sm 
				elif "ib1" in row['interface']:
					ib1_sm = sm
				else:
					raise CommandError(self, 'Subnet manager does not have ib0 nor ib1 interface')

			# Make sure we have the Default partition
			try:
				output = self.call('list.switch.partition', [sm, 'partition=Default'])
				if len(output) == 0:
					self.call('add.switch.partition', [sm, 'partition=Default', 'key=7fff'])
			except:
				raise CommandError(self, 'Can not add Default partition')

			# Get all the "partition.name*" attr and add it to the switch
			# and build the pdic so we can key off with the host later
			for row in self.call('list.host.attr', [sm, 'attr=partition.name*']):
				partition = row['value']
				key = row['attr']

				# Strip 'partition.name'
				key = key.split('.')[-1]

				# Add the partition to the switch
				try:
					self.call('add.switch.partition', [sm, 'partition=%s' % partition, 'key=%s' % key])
				except:
					raise CommandError(self, 'Can not add partition %s' % partition)
			
				pdic[key] = partition
				
		# Go through all the hosts and get the ib0/ib1 vlan
		# We use the vlan to get the partition name that
		# we need to attach to.
		for host in self.call('list.host', ['a:backend']):
			host_name = host['host']
			for row in self.call('list.host.interface', [host_name]):
				if row['interface'] == "ib0" or row['interface'] == "ib1":
					vlan = row['vlan']
					# If vlan is not set then don't need  to add to partition
					if vlan == None:
						continue

					# Partition this host belong to
					if str(vlan) in pdic:
						partition = pdic[str(vlan)]
					else:
						raise CommandError(self, 'Can not find partition for key "%s"' % vlan)

					# Add this host's guid to SM
					for row in self.call('list.host.attr', [host_name, "attr=*guid"]):
						if "ib0.guid" in row['attr']:
							guid = row['value']
							self.call('add.switch.partition.member',\
							          [ib0_sm, 'partition=%s' % partition,\
							          'member=%s' % guid])
						elif "ib1.guid" in row['attr']:
							guid = row['value']
							self.call('add.switch.partition.member',\
							          [ib1_sm, 'partition=%s' % partition,\
							          'member=%s' % guid])

					# Only need to do for one interface since
					# key of ib0 and ib1 is the same
					break

RollName = "stacki"
