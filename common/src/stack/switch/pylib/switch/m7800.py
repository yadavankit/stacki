import re

from stack.expectmore import ExpectMore
from stack.bool import str2bool
from . import Switch, SwitchException
from . import mellanoknok

partition_name = re.compile('  [a-z0-9]', re.IGNORECASE)
members_header = re.compile('  members', re.IGNORECASE)
guid_format = re.compile("([0-9a-f]{2}:){7}[0-9a-f]{2}|ALL", re.IGNORECASE)


class SwitchMellanoxM7800(Switch):
	"""
	Class for interfacing with a Mellanox 7800 Infiniband Switch.
	"""

	def __init__(self, switch_ip_address, switchname='switch', username='admin', password=''):
		# Grab the user supplied info, in case there is a difference (PATCH)
		self.switch_ip_address = switch_ip_address
		self.username = username
		self.password = password

		self.stacki_server_ip = None
		self.switchname = switchname
		self.proc = ExpectMore()
		self.proc.PROMPTS = (['.config. #', ' >', ' #'])


	def connect(self):
		"""
		Connect to the switch and get a configuration prompt
		"""
		ssh_options = '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -tt'
		self.proc.start(f'ssh {ssh_options} {self.username}@{self.switch_ip_address}')

		self.proc.wait(['Password:', ' >'])

		if self.proc.match_index == 0:
			# password-based auth
			self.proc.say(self.password)
		# otherwise, key-based auth is already setup

		login_seq = [
			([' >', ''], 'terminal length 999'),
			(' >', 'enable'),
			(' #', 'configure terminal'),
			('.config. #', ''),
		]

		self.proc.conversation(login_seq)

		self._api_connection = mellanoknok.Mellanoknok(self.switch_ip_address, password=self.password)


	def disconnect(self):
		self.proc.end('quit')


	@property
	def subnet_manager(self):
		""" get the subnet manager status for this switch """
		for line in self.proc.ask('show ib sm'):
			if 'enable' == line.strip():
				return True
		return False


	@subnet_manager.setter
	def subnet_manager(self, value):
		""" set the subnet manager status for this switch """
		cmd = 'ib sm'
		if value:
			self.proc.say(cmd)
		else:
			self.proc.say('no ' + cmd)


	def ssh_copy_id(self, pubkey):
		""" relies on pubkey being a string whose format is exactly that of "id_rsa.pub" """

		self.proc.say(f'ssh client user admin authorized-key sshv2 "{pubkey}"')


	@property
	def partitions(self):
		"""
		Return a dictionary of the partitions.
		partition['partition_name'] = {'pkey': int, 'ipoib': bool, 'guids': [list, of, member, guids]}
		"""

		partitions = {}
		cur_partition = None
		for line in self.proc.ask('show ib partition'):
			#print(line)
			if re.match(members_header, line):
				# drop the 'members' line, because it can look like partition names
				# lord help us if someone names their partition 'members'
				continue
			if re.match(partition_name, line):
				cur_partition = line.strip()
				partitions[cur_partition] = {
					'pkey': '',
					'ipoib': False,
					'guids': [],
				}
				continue

			line = line.strip()
			#print(line)
			if line.startswith('PKey'):
				_, key = line.split('=')
				partitions[cur_partition]['pkey'] = int(key, 16)
			elif line.startswith('ipoib'):
				_, ipoib = line.split('=')
				partitions[cur_partition]['ipoib'] = str2bool(ipoib.strip())
			elif line.startswith('GUID'):
				m = re.search(guid_format, line)
				partitions[cur_partition]['guids'].append(m.group(0))

		return partitions


	@property
	def interfaces(self):
		return self._api_connection.get_interfaces()


	def _validate_pkey(self, pkey):
		"""
		Valid pkey values are between 0x000 (2) to 0x7FFE (32766) (inclusive)
		0x7FFF is reserved for the Default partition.  0x0 is invalid
		"""

		pkey = int(pkey)
		if pkey < 2 and pkey > 32766:
			return None

		return hex(pkey)


	def add_partition(self, partition='Default', pkey=None):
		"""
		Add `partition` to the switch, with partition key `pkey` which must be between 2-32766.
		`partition` 'Default' has a hard-coded pkey.
		"""
		if partition != 'Default':
			if not pkey:
				raise SwitchException(f'a partition key is required for partition: {partition}.')
			pkey = self._validate_pkey(pkey)
			if not pkey:
				raise SwitchException('partition keys must be between 2 and 32766')

		if str(partition) == 'Default':
			add_part_seq = [
				(None, 'no ib partition Default'),
				("Type 'yes' to continue:", 'yes'),
				(self.proc.PROMPTS, 'ib partition Default pkey 0x7fff force'),
				(self.proc.PROMPTS, 'ib partition Default defmember limited force'),
				(self.proc.PROMPTS, 'ib partition Default ipoib force'),
				(self.proc.PROMPTS, None),
			]
			self.proc.conversation(add_part_seq)
		else:
			self.proc.say(f'ib partition {partition} pkey {pkey} force')


	def del_partition(self, partition):
		"""
		Remove `partition` from the switch.
		"""
		del_partition_seq = [(None, f'no ib partition {partition}')]
		if partition == 'Default':
			del_partition_seq.append(("Type 'yes' to continue:", 'yes'))
		self.proc.conversation(del_partition_seq + [(self.proc.PROMPTS, None)])


	def add_partition_member(self, partition, guid):
		"""
		Add a member to `partition` on the switch, identified by `guid`.
		"""
		m = re.fullmatch(guid_format, guid)
		if not m:
			raise SwitchException(f'GUID {guid} not valid')

		# too expensive?
		cur_partitions = self.partitions
		if partition not in cur_partitions:
			raise SwitchException(f'Partition {partition} does not exist')

		self.proc.say(f'ib partition {partition} member {guid} type full force')


	def del_partition_member(self, partition, guid):
		"""
		Remove a member from `partition` on the switch, identified by `guid`.
		"""
		m = re.fullmatch(guid_format, guid)
		if not m:
			raise SwitchException(f'GUID {guid} not valid')

		# too expensive?
		cur_partitions = self.partitions
		if partition not in cur_partitions:
			raise SwitchException(f'Partition {partition} does not exist')

		del_member_seq = [(None, f'no ib partition {partition} member {guid}')]
		if partition == 'Default':
			del_member_seq.append(("Type 'yes' to continue:", 'yes'))
		self.proc.conversation(del_member_seq + [(self.proc.PROMPTS, None)])
