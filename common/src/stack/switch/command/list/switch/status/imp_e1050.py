# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

from itertools import groupby
import json
import re
import requests
import stack.commands
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def natural_sort(s):
	return [int(''.join(g)) if k else ''.join(g) for k, g in groupby('\0' + s, str.isdigit)]


def net_show_interface(imp, switch):
	switch_name = switch['host']
	url = f'https://{switch["ip"]}:8080/nclu/v1/rpc'
	payload = {"cmd": "show interface json"}
	auth = (imp.owner.getHostAttr(switch_name, 'switch_username'),
	        imp.owner.getHostAttr(switch_name, 'switch_password'))
	headers = {'Content-Type': 'application/json'}

	data = json.loads(requests.post(url, headers=headers, json=payload, auth=auth, verify=False).text)
	for iface in sorted(data, key=natural_sort):
		port_match = re.search(r'\d+', iface)
		info = data[iface]
		if 'swp' in iface:
			iface_obj = info['iface_obj']

			port = port_match.group()
			vlan = '' if not iface_obj['vlan'] else iface_obj['vlan'][0]['vlan']  # handle multiple VLANs?

			imp.owner.addOutput(switch_name, [port, info['speed'], info['linkstate'], iface_obj['mac'], vlan, '', iface])  # host missing, switch hostfile?


class Implementation(stack.commands.Implementation):
	def run(self, args):
		switch = args[0]
		net_show_interface(self, switch)
