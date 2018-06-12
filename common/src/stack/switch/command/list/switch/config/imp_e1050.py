# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import json
import requests
import stack.commands
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def get_run_config(imp, args):
	switch = args[0]
	switch_name = switch['host']
	url = f'https://{switch["ip"]}:8080/nclu/v1/rpc'
	payload = {"cmd": f"show configuration"}
	auth = (imp.owner.getHostAttr(switch_name, 'switch_username'),
	        imp.owner.getHostAttr(switch_name, 'switch_password'))
	headers = {'Content-Type': 'application/json'}

	text = requests.post(url, headers=headers, json=payload, auth=auth, verify=False).text

	if imp.owner.raw:
		print(text)  # just print for raw?
	else:
		# data = json.loads(text)
		imp.owner.addOutput(switch_name, [])  # port, vlan, type -- these headers don't map well to the raw text



class Implementation(stack.commands.Implementation):
	def run(self, args):
		get_run_config(self, args)
		# is /tftpboot/pxelinux/stacki-232-32_running_config supposed to exist on FE? If so, net show config is irrelevant
