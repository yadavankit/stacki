# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import os
import time
import pexpect
import logging
from logging.handlers import RotatingFileHandler
import asyncio
import signal
import sys
import re


# A custom exception just so its easier to differentiate from Switch exceptions and system ones
class SwitchException(Exception):
	pass

class Switch():
	def __init__(self, switch_ip_address, switchname='switch', username='admin', password='admin'):
		# Grab the user supplied info, in case there is a difference (PATCH)
		self.switch_ip_address = switch_ip_address
		self.username = username
		self.password = password

		self.stacki_server_ip = None
		self.path = '/tftpboot/pxelinux'
		self.switchname = switchname
		self.check_filename = "%s/%s_check" % (self.path, self.switchname)
		self.download_filename = "%s/%s_running_config" % (self.path, self.switchname)
		self.upload_filename = "%s/%s_upload" % (self.path, self.switchname)

	def __enter__(self):
		# Entry point of the context manager
		return self

	def __exit__(self, *args):
		try:
			self.disconnect()
		except AttributeError:
			pass
			## TODO: release file lock here


class SwitchDellX1052(Switch):
	"""Class for interfacing with a Dell x1052 switch.
	"""

	def connect(self):
		"""Connect to the switch"""
		try:
			self.child = pexpect.spawn('ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -tt ' +
									   self.switch_ip_address)
			self._expect('User Name:', 10)
			self.child.sendline(self.username)
			self._expect('Password:')
			self.child.sendline(self.password)
		except:
			raise SwitchException("Couldn't connect to the switch")

	def disconnect(self):
		# q will exit out of an existing scrollable more/less type of prompt
		# Probably not necessary, but a bit safer

		# if there isn't an exit status
		# close the connection
		if not self.child.exitstatus:
			self.child.sendline("\nq\n")
			# exit should cleanly exit the ssh
			self.child.sendline("\nexit\n")
			# Just give it a few seconds to exit gracefully before terminate.
			time.sleep(3)
			self.child.terminate()
		

	def _expect(self, look_for, custom_timeout=15):
		try:
			self.child.expect(look_for, timeout=custom_timeout)
		except pexpect.exceptions.TIMEOUT:
			# print "Giving SSH time to close gracefully...",
			for _ in range(9, -1, -1):
				if not self.child.isalive():
					break
				time.sleep(1)
			debug_info = str(str(self.child.before) + str(self.child.buffer) + str(self.child.after))
			self.__exit__()
			raise SwitchException(self.switch_ip_address + " expected output '" + look_for +
							"' from SSH connection timed out after " +
							str(custom_timeout) + " seconds.\nBuffer: " + debug_info)
		except pexpect.exceptions.EOF:
			self.__exit__()
			raise SwitchException("SSH connection to " + self.switch_ip_address + " not available.")

	def get_mac_address_table(self):
		"""Download the mac address table"""
		time.sleep(1)
		command = 'show mac address-table'
		self.child.expect('console#', timeout=60)
		with open('/tmp/%s_mac_address_table' % self.switchname, 'wb') as macout:
			self.child.logfile = macout
			self.child.sendline(command)
			time.sleep(1)
			self.send_spacebar(4)
			self.child.expect('console#', timeout=60)
		self.child.logfile = None
	
	def parse_mac_address_table(self):
		"""Parse the mac address table and return list of connected macs"""
		_hosts = []
		with open('/tmp/%s_mac_address_table' % self.switchname, 'r') as f:
			for line in f.readlines():
				if 'dynamic' in line:
					# appends line to list
					# map just splits out the port 
					#   from the interface
					_hosts.append(list(
					  map(lambda x: x.split('/')[-1],
					  line.split())
					))

		return sorted(_hosts, key=lambda x: x[2])

	def get_interface_status_table(self):
		"""Download the interface status table"""
		time.sleep(1)
		command = 'show interface status'
		self.child.expect('console#', timeout=60)
		with open('/tmp/%s_interface_status_table' % self.switchname, 'wb') as macout:
			self.child.logfile = macout
			self.child.sendline(command)
			time.sleep(1)
			self.send_spacebar(4)
			self.child.expect('console#', timeout=60)
		self.child.logfile = None
	
	def parse_interface_status_table(self):
		"""Parse the interface status and return list of port information"""
		_hosts = []
		with open('/tmp/%s_interface_status_table' % self.switchname, 'r') as f:
			for line in f.readlines():
				if 'gi1/0/' in line:
					# appends line to list
					# map just splits out the port 
					#   from the interface
					_hosts.append(list(
					  map(lambda x: x.split('/')[-1],
					  line.split())
					))

		return _hosts


	def get_vlan_table(self):
		"""Download the vlan table"""
		time.sleep(1)
		command = 'show vlan'
		self.child.expect('console#', timeout=60)
		with open('/tmp/%s_vlan_table' % self.switchname, 'wb') as macout:
			print("opening vlan table file")
			self.child.logfile = macout
			self.child.sendline(command)
			time.sleep(1)
			self.send_spacebar(4)
			self.child.expect('console#', timeout=60)
		self.child.logfile = None

	def send_spacebar(self, times=1):
		"""Send Spacebar; Used to read more of the output"""
		command = "\x20"
		for i in range(times):
			self.child.send(command)
			time.sleep(1)

	def download(self, check=False):  # , source, destination):
		"""Download the running-config from the switch to the server"""
		time.sleep(1)
		if not check:
			_output_file = open(self.download_filename, 'w')
		else:
			_output_file = open(self.check_filename, 'w')
		os.chmod(_output_file.name, 0o777)
		_output_file.close()

		download_config = "copy running-config tftp://%s/%s" % (
			self.stacki_server_ip, 
			_output_file.name.split("/")[-1]
			)

		self.child.expect('console#', timeout=60)
		self.child.sendline(download_config)
		self._expect('The copy operation was completed successfully')

	def upload(self):
		"""Upload the file from the switch to the server"""

		upload_name = self.upload_filename.split("/")[-1]
		upload_config = "copy tftp://%s/%s temp" % (
				self.stacki_server_ip, 
				upload_name
				)
		apply_config = "copy temp running-config"
		self.child.expect('console#', timeout=60)
		self.child.sendline(upload_config)
		# Not going to look for "Overwrite file" prompt as it doesn't always show up.
		# self.child.expect('Overwrite file .temp.*\?')
		time.sleep(2)
		self.child.sendline('Y')  # A quick Y will fix the overwrite prompt if it exists.
		self._expect('The copy operation was completed successfully')
		self.child.sendline(apply_config)
		self._expect('The copy operation was completed successfully')

		self.download(True)
		# for debugging the temp files created:
		copied_file = open(self.check_filename).read()
		with open("/tftpboot/checker_file", "w") as f:
			f.write(copied_file)

		copied_file = open(self.upload_filename).read()
		with open("/tftpboot/upload_file", "w") as f:
			f.write(copied_file)


	def apply_configuration(self):
		"""Apply running-config to startup-config"""
		try:
			self.child.expect('console#')
			self.child.sendline('write')
			self.child.expect('Overwrite file .startup-config.*\?')
			self.child.sendline('Y')
			self._expect('The copy operation was completed successfully')
		except:
			raise SwitchException('Could not apply configuration to startup-config')
		
	def _vlan_parser(self, vlan_string):
		"""Takes input of a bunch of numbers in gives back a string containing all numbers once.
		The format for all_vlans is expected to be 3-7,9-10,44,3
		Which would be broken into a list like so: 3,4,5,6,7,9,10,44
		This if for inputing to the interface for the general port's vlan settings
		It could also be used to QA the vlans set afterwards. Which is not currently a feature."""
		clean_vlans = set()
		for each_vlan_str in vlan_string.split(","):
			if "-" in each_vlan_str:
				start, end = each_vlan_str.split("-")
				for each_number in range(int(start), int(end) + 1):
					clean_vlans.add(int(each_number))
			else:
				if each_vlan_str:
					clean_vlans.add(int(each_vlan_str))

		all_vlans = ','.join([str(vlan) for vlan in sorted(clean_vlans)])

		return all_vlans

	def get_port_from_interface(self, line):
		""" Get Port from gigabitethernet interface
		interface gigabitethernet1/0/20 returns 20
		"""
		port = line.split('/')[-1]
		return port

	def parse_config(self, config_filename):
		"""Parse the given configuration file and return a list of lists describing the vlan assignments per port."""
		my_list = []
		with open(config_filename) as filename:
			lines = filename.readlines()
		for line in lines:
			if "gigabitethernet" not in line and not parse_port:
				pass
			elif "interface gigabitethernet" in line:
				parse_port = int(line.strip().split("/")[-1:][0])
			elif "interface tengigabitethernet" in line:
				parse_port = int(line.strip().split("/")[-1:][0]) + 48
			elif "!" in line:
				parse_port = None
			elif parse_port:
				parse_vlan = None
				parse_mode = None
				parse_tagged = None
				current_port_properties = [parse_port, parse_mode, parse_vlan, parse_tagged]
				if "switchport" in line:
					current_port_properties = self._parse_switchport(current_port_properties, line)
				my_list[parse_port - 1] = current_port_properties
		return my_list

	def set_filenames(self, filename):
		"""
		Sets filenames for download, upload, and check files in /tftpboot/pxelinux
		"""
		self.switchname = filename
		self.download_filename = "%s/%s_running_config" % (self.path, self.switchname)
		self.upload_filename = "%s/%s_upload" % (self.path, self.switchname)
		self.check_filename = "%s/%s_check" % (self.path, self.switchname)


	def set_tftp_ip(self, ip):
		self.stacki_server_ip = ip


class SwitchInfiniBand(object):
	"""Class for interfacing with a Mellanox InfiniBand switch.
	"""
	_support_models = ["m7800"]

	def __init__(self, switch_ip_address, switchname='switch', username='admin', password='TD-Mellanox7800'):
		# Grab the user supplied info, in case there is a difference (PATCH)
		self.switch_ip_address = switch_ip_address
		self.username = username
		self.password = password

		self.stacki_server_ip = None
		self.switchname = switchname

	def __enter__(self):
		# Entry point of the context manager
		return self

	def __exit__(self, *args):
		try:
			self.disconnect()
		except AttributeError:
			pass
			## TODO: release file lock here

	def _expect(self, look_for, custom_timeout=15):
		""" Internal expect funtion to handle disconnections more gracefull."""
		try:
			self.child.expect(look_for, timeout=custom_timeout)
		except pexpect.exceptions.TIMEOUT:
			# print "Giving SSH time to close gracefully...",
			for _ in range(9, -1, -1):
				if not self.child.isalive():
					break
				time.sleep(1)
			debug_info = str(str(self.child.before) + str(self.child.buffer) + str(self.child.after))
			self.__exit__()
			raise SwitchException(self.switch_ip_address + " expected output '" + look_for +
							"' from SSH connection timed out after " +
							str(custom_timeout) + " seconds.\nBuffer: " + debug_info)
		except pexpect.exceptions.EOF:
			self.__exit__()
			raise SwitchException("SSH connection to " + self.switch_ip_address + " not available.")

	def _yes(self):
		"""Provide yes reply when needed"""
		self._expect('Type .yes. to continue:')
		self.child.sendline('yes')

	def connect(self):
		"""Connect to the switch"""
		try:
			self.child = pexpect.spawn('ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -tt ' +
			                           self.username + "@" + self.switch_ip_address)
			self._expect('Password:')
			self.child.sendline(self.password)
			self._expect(' >')
			self.child.sendline('terminal length 999')
			self._expect(' >')
			self.child.sendline('enable')
			self._expect(' #')
			self.child.sendline('configure terminal')
			self._expect('.config. #')
		except:
			raise SwitchException("Couldn't connect to switch: " + self.switch_ip_address)

	def disconnect(self):
		# if there isn't an exit status
		# close the connection
		if not self.child.exitstatus:
			self.child.sendline('quit')
			self.child.terminate()

	def show_ib_sm(self):
		try:
			self.child.sendline('show ib sm')
			self._expect('.config. #')
			output = self.child.before
			for line in output.splitlines():
				if "enable" in str(line):
					return "enable"

			return "disable"
		except:
			raise SwitchException("Couldn't show subnet manager on: " + self.switch_ip_address)

	def enable_ib_sm(self):
		try:
			self.child.sendline('ib sm')
			self._expect('.config. #')
		except:
			raise SwitchException("Couldn't enable subnet manager on: " + self.switch_ip_address)

	def disable_ib_sm(self):
		try:
			self.child.sendline('no ib sm')
			self._expect('.config. #')
		except:
			raise SwitchException("Couldn't disable subnet manager on: " + self.switch_ip_address)

	def show_partition(self, partition=None):
		if partition is None:
			self.child.sendline('show ib partition')
		else:
			cmd = "show ib partition " + str(partition)
			self.child.sendline(cmd)
		
		self._expect(' #')
		output = self.child.before

		# Filter output to get rid of expect garbage output
		filter_output = ""
		for line in output.splitlines():
			if "show ib partition" in str(line) or \
			   "Display partition information" in str(line) or \
			   "Pipe through a command" in str(line) or \
			   " (config)" in str(line) or \
			   re.match("^b'<cr>|^b'\\\\", str(line)):
				continue

			pattern = re.compile("^b'|^b\"|'$|\"$")
			filter_line = re.sub(pattern, "", str(line))
			if len(filter_line) == 0:
				continue

			filter_output += filter_line + "\n"

		if partition == "?":
			self.child.sendline("")

		return filter_output

	def del_partition(self, partition):
		cmd = "no ib partition " + str(partition) 
		self.child.sendline(cmd)

		# Need to confirm 'yes' if delete Default partition
		if str(partition) == "Default":
			self._yes()
	
	def _validate_pkey(self, pkey):
		"""
		Valid pkey values are between 0x000 (2) to 0x7FFE (32766) (inclusive)
		0x7FFF is reserved for the Default partition.  0x0 is an invalid P_KEY
		"""
	
		pkey = int(pkey)
		if pkey < 2 and pkey > 32766:
			return None

		pkey = hex(pkey)
		return pkey

	def add_partition(self, partition='Default', pkey=None):

		if str(partition) != "Default":
			pkey = self._validate_pkey(pkey)
			if pkey == None:
				raise SwitchException("Invalided partition key")
		
		try:
			if str(partition) == "Default":
				self.child.sendline('no ib partition Default')
				self._yes()
				self.child.sendline('ib partition Default pkey 0x7fff force')
				self.child.sendline('ib partition Default defmember limited force')
				self.child.sendline('ib partition Default ipoib force')
			else:
				cmd = "ib partition " + str(partition) + " pkey " + pkey + " force"
				self.child.sendline(cmd)
		except:
			raise SwitchException("Couldn't add partition " + partition + " on " + self.switch_ip_address)

	def _validate_guid(self, guid):
		"""
		guid format range 00:00:00:00:00:00:00:00 - ff:ff:ff:ff:ff:ff:ff:ff
		"""
		guid_format = re.compile("([0-9a-fA-F][0-9a-fA-F]:){7}[0-9a-fA-F][0-9a-fA-F]")
		guid_plain = re.compile("([0-9a-fA-F]){16}")
		
		guid = guid.lower()
		guid = guid.replace("0x", "")

		if guid_plain.match(guid):
			new_guid = ""
			for each in range(0, 16, 2):
				new_guid += guid[each:each + 2] + ":"

			guid = new_guid[:-1]
		
		if not guid_format.match(guid):
			return None

		return guid
	
	def show_partition_member(self, partition):
		cmd = "show ib partition " + str(partition) + " member"
		self.child.sendline(cmd)

		self._expect(' #')
		output = self.child.before
		return output

	def add_partition_member(self, partition, guid):

		_guid = self._validate_guid(guid)
		if _guid is None:
			raise SwitchException("GUID " + str(guid) + " is not valid")
	
		output = self.show_partition(partition)
		if "No partition named" in str(output):
			raise SwitchException("Partition " + str(partition)  + " does not exist")
	
		try:
			cmd = "ib partition " + partition + " member " + _guid + " type full force"
			self.child.sendline(cmd)
		except:
			raise SwitchException("Couldn't add " + str(guid) + " to  partition " + str(partition))


	def del_partition_member(self, partition, guid):

		output = self.show_partition(partition)
		if "No parttition named" in str(output):
			raise SwitchException("Partition " + str(partition)  + " does not exist")
		
		_guid = self._validate_guid(guid)
		if _guid is None:
			raise SwitchException("GUID " + str(guid) + " is not valid")

		try:
			cmd = "no ib partition " + partition + " member " + _guid
			self.child.sendline(cmd)
		except:
			raise SwitchException("Couldn't delete " + str(guid) + " from partition " + str(partition))
