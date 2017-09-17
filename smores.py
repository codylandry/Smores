from marshmallow import Schema, fields
from parser import to_jinja_template
from jinja2 import Template, Environment, contextfilter
from bs4 import BeautifulSoup as bs


def process_vars(var):
	if type(var) == list:
		try:
			return "".join([v['_default_template'] for v in var])
		except:
			return ''
	if type(var) == dict:
		try:
			return var['_default_template']
		except:
			return ''
	return var

env = Environment(finalize=process_vars)

class TemplateString(fields.Field):
	_CHECK_ATTRIBUTE = False

	def __init__(self, template_string, *args, **kwargs):
		super(TemplateString, self).__init__(*args, **kwargs)
		self.template_string = template_string
		self.dump_only = True

	def _serialize(self, value, attr, obj):
		schema = self.root.__class__
		template_fields = [k for k, v in self.root.declared_fields.items() if isinstance(v, TemplateString)]
		base_name = schema.__name__.lower()
		base_object = schema(exclude=template_fields).dump(obj).data # TODO - cache this
		context_dict = {base_name: base_object}
		context_dict.update(base_object)
		template = env.from_string(self.template_string)
		return template.render(**context_dict)

	def get_value(self, attr, obj, accessor=None, default=''):
		return obj

class TemplateFile(TemplateString):
	def __init__(self, template_path, *args, **kwargs):
		with open(template_path, 'rb') as template_file:
			template_string = template_file.read()
		super(TemplateFile, self).__init__(template_string, *args, **kwargs)

def render(data, schema, template_string):
	jinja_template = to_jinja_template(template_string)
	template = env.from_string(jinja_template)
	base_name = schema.__name__.lower()
	base_object = schema().dump(data).data
	context_dict = {base_name: base_object}
	context_dict.update(base_object)
	raw = template.render(**context_dict)
	soup = bs(raw, "html.parser")
	return soup.prettify()
