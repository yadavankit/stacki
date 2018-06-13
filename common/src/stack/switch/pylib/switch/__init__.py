# Copyright (c) 2006 - 2017 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

# check if these are removable
import asyncio
import logging
from logging.handlers import RotatingFileHandler
import signal
import sys


# A custom exception just so its easier to differentiate from Switch exceptions and system ones
class SwitchException(Exception):
	pass


class Switch:
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
