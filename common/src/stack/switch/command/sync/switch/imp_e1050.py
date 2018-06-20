# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import pexpect
import re
import stack.commands
from stack.switch.e1050 import SwitchCelesticaE1050


class Implementation(stack.commands.Implementation):
	def run(self, args):
		switch = args[0]

		self.switch_address = switch['ip']
		self.switch_name = switch['host']
		self.switch_username = self.owner.getHostAttr(self.switch_name, 'switch_username')
		self.switch_password = self.owner.getHostAttr(self.switch_name, 'switch_password')

		# self.ssh_copy_id()
		self.vlans()

	def ssh_copy_id(self):
		# handle invalid creds?
		child = pexpect.spawn(f'ssh-copy-id -i /root/.ssh/id_rsa.pub {self.switch_username}@{self.switch_address}')
		try:
			child.expect('password')
			child.sendline(self.switch_password)
			child.expect(pexpect.EOF)

			self.owner.addOutput(f'{self.switch_name}:', re.search(r'Number of (.+)', child.before.decode('utf-8')).group())
		except pexpect.EOF:
			self.owner.addOutput(f'{self.switch_name}:', re.findall(r'WARNING: (.+)', child.before.decode('utf-8'))[0])

	def vlans(self):
		with SwitchCelesticaE1050(self.switch_address, self.switch_name, self.switch_username, self.switch_password) as switch:
			host_ifaces = [hi for hi in self.owner.call('list.host.interface', ['output-format=json']) if hi['vlan'] is not None]
			vlans = ','.join(set(str(hi['vlan']) for hi in host_ifaces))
			switch.rpc_req_text(cmd=f"add vlan {vlans}")

			# better names?
			mac_ifaces = {}
			for item in self.owner.call('list.switch.mac', ['output-format=json']):  # pinghost=True (broken), maybe unneeded
				mac_ifaces[item['mac']] = {'iface': 'swp' + item['port'], 'vlan': item['vlan']}  # add vlan at this point or not?
				# if so, why not just rpc_req_text here? all the info is here
				# but might 'list switch mac' include non-vlan ports in the future?

			for host_iface in host_ifaces:
				iface = mac_ifaces[host_iface['mac']]

				switch.rpc_req_text(cmd=f"add interface {iface['iface']} bridge access {host_iface['vlan']}")

			# `net commit`
