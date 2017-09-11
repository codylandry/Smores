from marshmallow import Schema, fields
from jinja2 import Template, Environment, contextfilter
Schema.template = staticmethod(lambda: 'default template')
from sample_data import SAMPLE_DATA
from pydash import get
from inspect import isclass

@contextfilter
def get_data(context, path):
	data = context['data']
	value = get(data, path)
	template_func = get_schema_endpoint(data['base_schema'], path)
	if template_func:
		return template_func(value)
	return value

env = Environment()
env.filters['get_data'] = get_data

def render_schema_template_function(schema):
	func = getattr(schema, 'smores_template', None)
	if not func:
		return None

	if not isclass(schema):
		schema = schema.__class__

	def return_func(data):
		template = env.from_string(func())
		data.update({'base_schema': schema})
		return template.render(data=data)
	return return_func

def get_schema_endpoint(schema, path):
	current_node = schema
	path_parts = path.split('.')

	if (len(path_parts) == 1) and (schema.__name__.lower() == path_parts[0]):
		return render_schema_template_function(schema)

	start = 1 if schema.__name__.lower() == path_parts[0] else 0

	for part in path_parts[start:]:
		node = getattr(current_node, '_declared_fields', None)
		if node:
			current_node = node[part]

		node_schema = getattr(current_node, 'schema', None)
		if node_schema:
			current_node = node_schema
	return render_schema_template_function(current_node)


def render(data, schema, base_template):
	base_name = schema.__name__.lower()
	base_object = schema().dump(data).data
	context_dict = {base_name: base_object, 'base_schema': schema}
	context_dict.update(base_object)
	template = env.from_string(base_template)
	return template.render(data=context_dict)


class Coordinates(Schema):
	lat = fields.Decimal()
	lng = fields.Decimal()

	@staticmethod
	def smores_template():
		return """
			<ul>
				Coordinates
				<li>lat: {{ 'lat' | get_data }}</li>
				<li>lng: {{ 'lng' | get_data }}</li>
			</ul>
			"""


class Address(Schema):
	street = fields.String()
	suite = fields.String()
	city = fields.String()
	zipcode = fields.String()
	geo = fields.Nested(Coordinates)

	@staticmethod
	def smores_template():
		return """
			<div>
				Address
				<div>street: {{ 'street' | get_data }}</div>
				<div>suite: {{ 'suite' | get_data }}</div>
				<div>city: {{ 'city' | get_data }}</div>
				<div>zipcode: {{ 'zipcode' | get_data }}</div>
				<div>
					{{ 'geo' | get_data }}
				</div>
			</div>
			"""


class Company(Schema):
	name = fields.String()
	catchPhrase = fields.String()
	bs = fields.String()

	@staticmethod
	def smores_template():
		return """
			<div>
				Company
				<div>name: {{ 'name' | get_data }}</div>
				<div>catchPhrase: {{ 'catchPhrase' | get_data }}</div>
				<div>bs: {{ 'bs' | get_data }}</div>
			</div>
			"""


class User(Schema):
	id = fields.Integer()
	name = fields.String()
	email = fields.Email()
	address = fields.Nested(Address)
	phone = fields.String()
	website = fields.String()
	company = fields.Nested(Company)

	@staticmethod
	def smores_template():
		return """
			<div>
				this is from the user schema
				{{ 'id' | get_data }}
				{{ 'name' | get_data }} 
				{{ 'email' | get_data }} 
				{{ 'address' | get_data }} 
				{{ 'phone' | get_data }} 
				{{ 'website' | get_data }} 
				{{ 'company.name' | get_data }} 
			</div>
			"""

BASE_TEMPLATE = """
	<div>
		<div>{{ 'user.address.city' | get_data }}</div>
	</div>
"""

print render(SAMPLE_DATA[0], User, BASE_TEMPLATE)
