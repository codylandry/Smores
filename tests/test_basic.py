from smores import Smores
from smores.parser import to_jinja_template
from sample_data import users, register_schemas
import pytest

@pytest.fixture(scope='module')
def smores_instance():
	smores = Smores()
	register_schemas(smores)
	return smores

# ------------------------------------------------------------------------------
parser_test_cases = [
	("{user.name}", "{{user.name}}"),
	("{user.dogs:1}", "{{user.dogs[0]}}"),
	("{user.dogs:1.name}", "{{user.dogs[0].name}}"),
	("{user.addresses:4.geo.lat}", "{{user.addresses[3].geo.lat}}"),
]

@pytest.mark.parametrize("input, output", parser_test_cases)
def test_parser(input, output):
	result = to_jinja_template(input)
	assert result == output

# ------------------------------------------------------------------------------
default_template_cases = [
	("{user}", "Leanne Graham---Sincere@april.biz"),
	("{user.address}", "Kulas Light---Gwenborough----37.3159,81.1496"),
	("{user.address.geo}", "-37.3159,81.1496"),
	("{user.company}", "Romaguera-Crona---Multi-layered client-server neural-net---harness real-time e-markets"),
]

@pytest.mark.parametrize("input, output", default_template_cases)
def test_render_default_template(smores_instance, input, output):
	result = smores_instance.render(dict(user=users[0]), input)
	assert result == output

# ------------------------------------------------------------------------------
non_default_template_strings = [
	("{user.long_template}", "Leanne Graham--1-770-736-8031 x56442--Sincere@april.biz--hildegard.org---37.3159,81.1496"),
	("{user.dogs:0.with_greeting}", "Hi, this is my dog Spot"),
]

@pytest.mark.parametrize("input, output", non_default_template_strings)
def test_non_default_template_strings(smores_instance, input, output):
	result = smores_instance.render(dict(user=users[0]), input)
	assert result == output

# ------------------------------------------------------------------------------
bad_input_cases = [
	# bad data inputs
	([], "{user}"),
	("some string, should be a dict", "{user}"),
	(1234, "{user}"),

	# bad template string inputs
	(dict(user=users[0]), 123),
	(dict(user=users[0]), dict()),
	(dict(user=users[0]), []),
	(dict(user=users[0]), users[0]),
]
@pytest.mark.parametrize("input", bad_input_cases)
def test_bad_render_inputs(smores_instance, input):
	data, template = input
	with pytest.raises(Exception):
		smores_instance.render(data, template)
