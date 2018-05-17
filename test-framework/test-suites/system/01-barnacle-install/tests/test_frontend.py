import pytest


def test_frontend_stack_report_system(host):
	"Simple sanity test that a frontend is up and running"

	# We have to run sudo ourselves because stack report system needs to be ran
	# as an login shell for its tests to pass
	cmd = host.run("sudo -i stack report system")

	assert cmd.rc == 0

@pytest.mark.parametrize("backend", ("backend-0-0", "backend-0-1"))
def test_frontend_ssh_to_backends(host, backend):
	"Test that the frontend can SSH to its backends"

	cmd = host.run("sudo -i ssh %s hostname" % backend)
	
	assert cmd.rc == 0
	assert cmd.stdout.strip().split('.')[0] == backend

@pytest.mark.parametrize("backend", ("backend-0-0", "backend-0-1"))
def test_frontend_gathered_backend_nics(host, backend):
	"Test that the frontend grabbed all backend nics"
	# Each of these commands are off by one, the header for stack list, and the loppback for find /sys/class/net/
	cmd = host.run("sudo -i ssh %s 'find /sys/class/net/* -maxdepth 0 | wc -l'" % backend)
	assert cmd.rc == 0
	nic_count = int(cmd.stdout)
	result = host.run("sudo -i stack list host interface %s" % backend)
	assert cmd.rc == 0
	assert nic_count == len(result.stdout.splitlines())

def test_default_appliances_have_sane_attributes(host):
	"Test that default appliances are created with expected attrs"

	expected_output = host.run("cat /export/test-files/default_appliance_attrs_output.json")

	cmd = host.run("sudo -i stack list appliance attr output-format=json")

	assert cmd.rc == 0
	assert cmd.stdout.strip() == expected_output.stdout.strip()
