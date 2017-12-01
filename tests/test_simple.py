from smores import Smores, AutocompleteResponse, __version__, Schema, Nested
from smores.parser import to_jinja_template
from smores.utils import loop_table_rows, get_module_schemas
from sample_data import users
from create_db import User, db_session, select
import pytest
from marshmallow import fields
import schemas_module



@pytest.fixture(scope='module')
def smores_instance():
	smores = Smores()
	smores.add_module_schemas(schemas_module)
	return smores



# ------------------------------------------------------------------------------
def test_get_version():
	assert bool(__version__)

# ------------------------------------------------------------------------------
parser_test_cases = [
	("{user.name}", "{{user.name | default('')}}"),
	("{user.dogs:1}", "{{user.dogs[0] | default('')}}"),
	("{user.dogs:1.name}", "{{user.dogs[0].name | default('')}}"),
	("{user.addresses:4.geo.lat}", "{{user.addresses[3].geo.lat | default('')}}"),
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
	('{user.dogs}', 'Name: RufusName: SnoopyName: ScratchName: Spot'),
	("{user.address.geo.lat}", "-37.3159"),
	("{user.company}", "Romaguera-Crona---Multi-layered client-server neural-net---harness real-time e-markets"),
	("{user.basic}", "<div>Leanne Graham</div><div>Sincere@april.biz</div>")
]

@pytest.mark.parametrize("input, output", default_template_cases)
def test_render_default_template_with_dicts(smores_instance, input, output):
	result = smores_instance.render(dict(user=users[0]), input)
	assert result == output

@pytest.mark.parametrize("input, output", default_template_cases)
def test_render_default_template_with_models(smores_instance, input, output):
	with db_session:
		result = smores_instance.render(dict(user=users[0]), input)
		assert result == output

def test_access_list_with_no_default_template():
	# creates schema with no _default_template and attempts to access it directly from a nested
	# field with many = True
	class NoTemplateDog(Schema):
		name = fields.String()

	class TestUser(Schema):
		dogs = Nested(NoTemplateDog, many=True)

	smores_instance = Smores()
	template = "{TestUser.dogs}"
	with smores_instance.with_schemas([NoTemplateDog, TestUser]):
		result = smores_instance.render(dict(testuser=users[0]), template)
	assert result == ""

# ------------------------------------------------------------------------------
non_default_template_strings = [
	("{user.long_template}", "Leanne Graham--1-770-736-8031 x56442--Sincere@april.biz--hildegard.org--"),
]

@pytest.mark.parametrize("input, output", non_default_template_strings)
def test_non_default_template_strings_with_dicts(smores_instance, input, output):
	result = smores_instance.render(dict(user=users[0]), input)
	assert result == output

@pytest.mark.parametrize("input, output", non_default_template_strings)
def test_non_default_template_strings_with_models(smores_instance, input, output):
	with db_session:
		result = smores_instance.render(dict(user=User[1]), input)
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
	("", AutocompleteResponse('INVALID', ['address', 'company', 'coordinates', 'dog', 'user'], "")),
	("user", AutocompleteResponse('VALID', ['_default_template', 'address', 'basic', 'company',
	                                           'dogs', 'email', 'id', 'long_template', 'name', 'phone', 'website'], "user")),
	("u", AutocompleteResponse('INVALID', ['user'], "")),
	("user.a", AutocompleteResponse('INVALID', ['address'], "user")),
	("user.dogs", AutocompleteResponse('INVALID', [':1'], "user")),
	("user.dogs:1", AutocompleteResponse('INVALID', ['_default_template', 'dog', 'name', 'with_greeting'], "user.dogs:1")),
	("user.dogs:1.name", AutocompleteResponse('VALID', [], "user.dogs:1.name")),
	("coordinates", AutocompleteResponse('INVALID', ['lat', 'lng'], "coordinates")),
	("address.geo", AutocompleteResponse('INVALID', ['lat', 'lng'], "address.geo")),
	("some.garbage", AutocompleteResponse('INVALID', [], "")),
	("user.garbage", AutocompleteResponse('INVALID', [], "user")),
	("user.address.garbage", AutocompleteResponse('INVALID', [], "user.address")),
	("user.aliases.garbage", AutocompleteResponse('INVALID', [], "user")),
	("user.aliases:1.garbage", AutocompleteResponse('INVALID', [], "user")),
]

@pytest.mark.parametrize("input, output", autocomplete_cases)
def test_autocomplete(smores_instance, input, output):
	assert smores_instance.autocomplete(input) == output

autocomplete_only_cases = [
	('user', AutocompleteResponse('INVALID', [], "")),
	('u', AutocompleteResponse('INVALID', [], "")),
	('a', AutocompleteResponse('INVALID', ['address'], "")),
	('address.geo', AutocompleteResponse('INVALID', ['lat', 'lng'], "address.geo")),
]

@pytest.mark.parametrize("input, output", autocomplete_only_cases)
def test_autocomplete_only(smores_instance, input, output):
	result = smores_instance.autocomplete(input, only=['address'])
	assert result == output

autocomplete_exclude_cases = [
	('user', AutocompleteResponse('VALID', ['_default_template', 'address', 'basic', 'company',
	                                           'dogs', 'email', 'id', 'long_template', 'name', 'phone', 'website'], "user")),
	('u', AutocompleteResponse('INVALID', ['user'], "")),
	('a', AutocompleteResponse('INVALID', [], "")),
	('address.geo', AutocompleteResponse('INVALID', [], "")),
]

@pytest.mark.parametrize("input, output", autocomplete_exclude_cases)
def test_autocomplete_exclude(smores_instance, input, output):
	result = smores_instance.autocomplete(input, exclude=['address'])
	assert result == output

# ------------------------------------------------------------------------------
def test_temp_schemas_single(smores_instance):
	class Event(Schema):
		tech = fields.String()
		location = fields.String()

	event = dict(tech="Tom Johnson", location="South Broad St.")
	data = dict(user=users[0], event=event)
	template = "{user}--{event.tech}"
	expected_outcome = "Leanne Graham---Sincere@april.biz--Tom Johnson"

	with smores_instance.with_schemas(Event):
		assert smores_instance.render(data, template) == expected_outcome

def test_temp_schemas_list(smores_instance):
	class Event(Schema):
		tech = fields.String()
		location = fields.String()

	event = dict(tech="Tom Johnson", location="South Broad St.")
	data = dict(user=users[0], event=event)
	template = "{user}--{event.tech}"
	expected_outcome = "Leanne Graham---Sincere@april.biz--Tom Johnson"

	with smores_instance.with_schemas([Event]):
		assert smores_instance.render(data, template) == expected_outcome

# ------------------------------------------------------------------------------
fallback_cases = [
	(None, "Leanne Graham--Sincere@april.biz--"),
	("INVALID_TAG", "Leanne Graham--Sincere@april.biz--INVALID_TAG"),
	(lambda tag: "!!%s!!" % tag, "Leanne Graham--Sincere@april.biz--!!{user.notarealtag}!!")
]
@pytest.mark.parametrize("fallback_value, output", fallback_cases)
def test_smores_fallback_string(smores_instance, fallback_value, output):
	template = "{user.name}--{user.email}--{user.notARealTag}"
	result = smores_instance.render(dict(user=users[0]), template, fallback_value=fallback_value)
	assert  result == output

# ------------------------------------------------------------------------------
def test_subtemplates(smores_instance):
	sub_templates = {
		"subtemplate1": "{user.name}--{user.website}",
		"subtemplate2": "{user.email}--{user.phone}",
	}

	data = dict(user=users[0])
	template = "{subtemplate1}---{subtemplate2}"
	expected_outcome = "Leanne Graham--hildegard.org---Sincere@april.biz--1-770-736-8031 x56442"
	assert smores_instance.render(data, template, sub_templates=sub_templates) == expected_outcome

# ------------------------------------------------------------------------------
def test_repeating_table_rows_func(smores_instance):
	iterable_tags = {
		"mydogs.*": ("mydogs", "user.dogs")
	}

	template = "<table><tr><td>{mydogs.name}</td></tr><tr><td>{mydogs.name}</td></tr></table>"

	result = loop_table_rows(iterable_tags, template)
	expected_output = "<table>{% for mydogs in user.dogs %}<tr><td>{mydogs.name}</td></tr><tr><td>{mydogs.name}</td></tr>{% endfor %}</table>"
	assert result == expected_output

# ------------------------------------------------------------------------------
def test_render_preprocess_func(smores_instance):
	def prepend_word(temp):
		res = "word---" + temp
		return res

	template = "{user.name}"
	result = smores_instance.render(dict(user=users[0]), template, pre_process=prepend_word)
	assert result == "word---Leanne Graham"

# ------------------------------------------------------------------------------
def test_invalid_root_attr(smores_instance):
	# def prepend_word(temp):
	# 	res = "{{invalid_root.dog}}---" + temp
	# 	return res
	template = "{user.invalid_root.dog}"
	result = smores_instance.render(dict(user=users[0]), template)
	assert result == ''

def test_invalid_root_attr_w_model(smores_instance):
	with db_session:
		template = "{user.invalidattr.dog}"
		result = smores_instance.render(dict(user=User[1]), template)
		assert result == ''

# ------------------------------------------------------------------------------
def test_get_module_schemas():
	smores = Smores()
	schemas = get_module_schemas(schemas_module)
	smores.add_schemas(schemas)
	res = smores.render(dict(user=users[0]), "{user.name}")
	assert res == 'Leanne Graham'

# ------------------------------------------------------------------------------
def test_add_module_schemas():
	smores = Smores()
	smores.add_module_schemas(schemas_module)
	res = smores.render(dict(user=users[0]), "{user.name}")
	assert res == 'Leanne Graham'

