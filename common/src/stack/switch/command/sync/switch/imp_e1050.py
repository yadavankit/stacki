# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import pexpect
import re
import stack.commands


def ssh_copy_id(imp, switch):
	switch_address = switch['ip']
	switch_name = switch['host']
	switch_username = imp.owner.getHostAttr(switch_name, 'switch_username')
	switch_password = imp.owner.getHostAttr(switch_name, 'switch_password')

	child = pexpect.spawn(f'ssh-copy-id -i /root/.ssh/id_rsa.pub {switch_username}@{switch_address}')
	try:
		child.expect('password')
		child.sendline(switch_password)
		child.expect(pexpect.EOF)
		print(re.search(r'Number of (.+)', child.before.decode('utf-8')).group())
	except pexpect.EOF:
		print(re.findall(r'WARNING: (.+)', child.before.decode('utf-8'))[0])


class Implementation(stack.commands.Implementation):
	def run(self, args):
		switch = args[0]
		ssh_copy_id(self, switch)