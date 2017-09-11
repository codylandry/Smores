from marshmallow import Schema, fields
from jinja2 import Template, Environment, contextfilter
Schema.smores_template = staticmethod(lambda: 'default template')
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
