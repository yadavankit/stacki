# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import re
import stack.commands
from stack.exception import CommandError
from stack.switch import SwitchInfiniBand, SwitchException


class Implementation(stack.commands.Implementation):
	def run(self, args):

		switch = args[0]
		switch_address = switch['ip']
		switch_name = switch['host']
		switch_username = self.owner.getHostAttr(switch_name, 'switch_username')
		switch_password = self.owner.getHostAttr(switch_name, 'switch_password')
		
		partition = None
		if len(args[1]) > 0:
			partition = args[1]['partition']

		# Check if the switch has an ip address
		if not switch_address:
			raise CommandError(self, '"%s" has no address to connect to.' % switch_name)

		# Interface should be ib0 or ib1
		for output in self.owner.call('list.host.interface', [switch_name]):
			interface = output['interface']
			if interface != "ib0" and interface !="ib1":
				raise CommandError(self, '"%s" interface is not "ib0" nor "ib1".' % switch_name)


		# Read the switch partition information in the raw format
		# and display it in a pretty format
		with SwitchInfiniBand(switch_address, switch_name, switch_username, switch_password) as switch:
			try:
				switch.connect()

				# If partition is not giving then get all partition name first
				# so we can traverse them to get each partion information
				plist = []
				if partition == None:
					output = switch.show_partition(None)
					for line in output.split("\n"):
						if re.match("  [a-zA-Z0-9]", line) and not \
						   re.match("  members", line):
							plist.append(line)
				else:
					plist.append(partition)
		
				# For each partition, get its pkey and members
				for partition in plist:
					member = False
					key = None 
					guids = []
					output = switch.show_partition(partition)
					for line in output.split("\n"):
						if " PKey " in line:
							_,key = line.split("=")
							# Convert key to interger since we store it
							# as interger in the host's VLAN
							key = int(key, 16)
						elif " GUID=" in line:
							guid_format = re.compile("([0-9a-fA-F][0-9a-fA-F]:){7}[0-9a-fA-F][0-9a-fA-F]|ALL")
							m = re.search(guid_format, line)
							guids.append(m.group(0))

					# Now search through all hosts and match the guids
					# to the host's guid.
					for guid in guids:
						if "ALL" in guid:
							member = True
							self.owner.addOutput(switch_name, [partition, key, guid, "ALL", interface])
							continue

						for line in self.owner.call('list.host.attr', ["a:backend", "attr=*.guid"]):
							if line['value'] in guid:
								host = line['host']
								member = True
								self.owner.addOutput(switch_name, [partition, key, guid, host, interface])
					
					if key and not member:				
						self.owner.addOutput(switch_name, [partition, key, "------", "----", interface])

			except SwitchException as switch_error:
				raise CommandError(self, switch_error)
			except Exception as yo:
			#except:
				print("switch_name: " + str(switch_name))
				print("ERROR_2: " + str(yo))
				raise CommandError(self, "There was an error getting the partition of the switch.")

RollName = "stacki"
