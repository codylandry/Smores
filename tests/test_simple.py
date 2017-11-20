from smores import Smores, TagAutocompleteResponse
from smores.parser import to_jinja_template
from sample_data import users, register_schemas
from create_db import User, db_session, select
import pytest

@pytest.fixture(scope='module')
def smores_instance():
	smores = Smores()
	register_schemas(smores)
	return smores

# ------------------------------------------------------------------------------
parser_test_cases = [
	("{user.name}", '{{user.name | default("")}}'),
	("{user.dogs:1}", '{{user.dogs[0] | default("")}}'),
	("{user.dogs:1.name}", '{{user.dogs[0].name | default("")}}'),
	("{user.addresses:4.geo.lat}", '{{user.addresses[3].geo.lat | default("")}}'),
]

@pytest.mark.parametrize("input, output", parser_test_cases)
def test_parser(input, output):
	result = to_jinja_template(input)
	assert result == output

# ------------------------------------------------------------------------------
default_template_cases = [
	("{user}", "Leanne Graham---Sincere@april.biz"),
	("{user.address}", "Kulas Light---Gwenborough---"),
	("{user.address.geo}", ""),
	("{user.address.geo.lat}", "-37.3159"),
	("{user.company}", "Romaguera-Crona---Multi-layered client-server neural-net---harness real-time e-markets"),
]

@pytest.mark.parametrize("input, output", default_template_cases)
def test_render_default_template_with_dicts(smores_instance, input, output):
	result = smores_instance.render(dict(user=users[0]), input)
	assert result == output

@pytest.mark.parametrize("input, output", default_template_cases)
def test_render_default_template_with_models(smores_instance, input, output):
	with db_session:
		result = smores_instance.render(dict(user=User[1]), input)
		assert result == output

# ------------------------------------------------------------------------------
non_default_template_strings = [
	("{user.long_template}", "Leanne Graham--1-770-736-8031 x56442--Sincere@april.biz--hildegard.org--"),
	("{user.dogs:1.with_greeting}", "Hi, this is my dog Rufus"),
]

@pytest.mark.parametrize("input, output", non_default_template_strings)
def test_non_default_template_strings_with_dicts(smores_instance, input, output):
	user = users[0]
	user['dogs'] = sorted(user['dogs'], key=lambda d: d['name'])
	result = smores_instance.render(dict(user=users[0]), input)
	assert result == output

non_default_template_strings = [
	("{user.long_template}", "Leanne Graham--1-770-736-8031 x56442--Sincere@april.biz--hildegard.org--"),
	("{user.dogs:0.with_greeting}", "Hi, this is my dog Spot"),
]

@pytest.mark.parametrize("input, output", non_default_template_strings)
def test_non_default_template_strings_with_models(smores_instance, input, output):
	with db_session:
		user = User[1]
		user.dogs = user.dogs.sort_by(lambda d: d.name)
		result = smores_instance.render(dict(user=user), input)
		assert result == output

# ------------------------------------------------------------------------------
with db_session:
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
		(dict(user=User[1]), 123),
		(dict(user=User[1]), dict()),
		(dict(user=User[1]), []),
		(dict(user=User[1]), users[0]),

	]
@pytest.mark.parametrize("input", bad_input_cases)
def test_bad_render_inputs(smores_instance, input):
	data, template = input
	with pytest.raises(Exception):
		smores_instance.render(data, template)

# ------------------------------------------------------------------------------
autocomplete_cases = [
	("user", TagAutocompleteResponse('VALID', ['_default_template', 'address', 'company',
	                                           'dogs', 'email', 'id', 'long_template', 'name', 'phone', 'website'])),
	("u", TagAutocompleteResponse('INVALID', ['user'])),
	("user.a", TagAutocompleteResponse('INVALID', ['address'])),
	("user.dogs", TagAutocompleteResponse('INVALID', [':1'])),
	("user.dogs:1", TagAutocompleteResponse('INVALID', ['_default_template', 'name', 'with_greeting'])),
	("user.dogs:1.name", TagAutocompleteResponse('VALID', [])),
	("address.geo", TagAutocompleteResponse('INVALID', ['lat', 'lng'])),
	("some.garbage", TagAutocompleteResponse('INVALID', [])),
	("user.garbage", TagAutocompleteResponse('INVALID', [])),
	("user.address.garbage", TagAutocompleteResponse('INVALID', [])),
	("user.aliases.garbage", TagAutocompleteResponse('INVALID', [])),
	("user.aliases:1.garbage", TagAutocompleteResponse('INVALID', [])),
]

@pytest.mark.parametrize("input, output", autocomplete_cases)
def test_tag_autocomplete(smores_instance, input, output):
	assert smores_instance.tag_autocomplete(input) == output
