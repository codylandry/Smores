from marshmallow import Schema, fields
from parser import to_jinja_template
from jinja2 import Template, Environment, contextfilter
from bs4 import BeautifulSoup as bs
import inspect
import os
from parser import ATTR, delimitedList


class TemplateString(fields.Field):
	"""
	This field takes a jinja template as an argument and returns the rendered the template during serialization
	"""
	# TemplateStrings never map to a particular value on the obj, but rather, the whole object
	_CHECK_ATTRIBUTE = False

	def __init__(self, template_string, env=None, use_parser=False, *args, **kwargs):
		super(TemplateString, self).__init__(*args, **kwargs)

		# the template string to be rendered
		if use_parser:
			template_string = to_jinja_template(template_string)
		self.template_string = template_string

		# TemplateStrings do not get 'loaded' by marshmallow
		self.dump_only = True
		self.env = env

	def _serialize(self, _, __, obj):
		"""
		Returns rendered jinja template using obj.
		:param obj: the unserialized obj
		:return: rendered template text
		"""
		# get schema class
		schema = self.root.__class__

		# get names of all TemplateString/TemplateFile fields for the schema
		template_fields = [k for k, v in self.root.declared_fields.items() if isinstance(v, TemplateString)]

		# serialize remaining fields of schema for template context
		context = schema(exclude=template_fields).dump(obj).data  # TODO - cache this

		# return rendered template

		template = self.env.from_string(self.template_string)
		return template.render(**context)

	def get_value(self, attr, obj, accessor=None, default=''):
		return obj


class TemplateFile(TemplateString):
	"""
	Allows ability to store templates in files
	"""

	def __init__(self, template_path, env=None, use_parser=False, *args, **kwargs):
		# grab the template file
		with open(template_path, 'rb') as template_file:
			template_string = template_file.read()
		# pass it on to TemplateString
		super(TemplateFile, self).__init__(template_string, env=env, use_parser=use_parser, *args, **kwargs)


class SmoresEnvironment(Environment):
	def __init__(self, fallback_value='', *args, **kwargs):
		super(SmoresEnvironment, self).__init__(*args, **kwargs)
		self.fallback_value = fallback_value

	def getattr(self, obj, attribute):
		try:
			return super(SmoresEnvironment, self).getattr(obj, attribute)
		except:
			return self.fallback_value

	def getitem(self, obj, attribute):
		try:
			return super(SmoresEnvironment, self).getitem(obj, attribute)
		except:
			return self.fallback_value


class Smores(object):
	schemas = []

	def __init__(self, default_template_name='_default_template', fallback_value=''):
		self._DEFAULT_TEMPLATE = default_template_name
		self.fallback_value = fallback_value

		# This jinja environment sets up a function to process variables into either serialized form or template
		self.env = SmoresEnvironment(fallback_value=fallback_value, finalize=self.process_vars())
		self.user_templates = {}

	def process_vars(self):
		"""
		Does final processing of variables resolved by jinja.
		A dict means we have the result of a single schema dump.
		A list means we have the result of a dump of a list of schemas.
		For both cases, we attempt to get the _default_template of the schemas
		:param var: the value resolved by jinja for a variable
		:return: value to be rendered (string or template)
		"""
		_DEFAULT_TEMPLATE = self._DEFAULT_TEMPLATE
		fallback_value = self.fallback_value
		def process(var):
			if type(var) == list:
				# if var is a list return the _default_template for each item
				try:
					return "".join([v[_DEFAULT_TEMPLATE] for v in var])
				except:
					return fallback_value
			if type(var) == dict:
				# if var is a dict, then we must be returning a single schema, so try to get the _default_template
				try:
					return var[_DEFAULT_TEMPLATE]
				except:
					return fallback_value
			# fallback to just returning the var as is (a plain field value)
			return var
		return process

	def schema(self, schema):
		Smores.schemas.append(schema)
		return schema

	def tag_autocomplete(self, tag):
		"""
			Gets the available options for a given tag fragment
			:param base_schema: The schema the template was written for
			:param tag: a tag fragment ex: user.addresses
			:return:
			"""
		tag = tag.strip()
		attrs = delimitedList(ATTR.setParseAction(lambda x: x[0]), delim='.')
		attrs = attrs.parseString(tag)

		if tag == '':
			return [s.__name__ for s in Smores.schemas]

		root_schema = next((s for s in Smores.schemas if s.__name__.lower() == attrs[0].lower()), None)
		if root_schema:
			current_node = root_schema()
		else:
			return []
		for attr in attrs:
			if attr.lower() == current_node.__class__.__name__.lower():
				continue
			try:
				node = current_node.declared_fields[attr]
				if isinstance(node, fields.Nested):
					current_node = node.schema
				else:
					current_node = node
			except:
				continue

		if isinstance(current_node, (Schema,)):
			return current_node.declared_fields.keys()
		else:
			return []

	def TemplateString(self, *args, **kwargs):
		return TemplateString(*args, env=self.env, **kwargs)

	def TemplateFile(self, *args, **kwargs):
		return TemplateFile(*args, env=self.env, **kwargs)

	def render(self, data, template_string, sub_templates=None):
		"""
		Recursively populates the 'template_string' with data gathered from dumping 'data' through the Marshmallow 'schema'.
		Variables are evaluated and will return the '_default_template' if one exists.  Prettifies end result.
		:param data: data to be dumped via the 'schema' (likely an ORM model instance) accepts both objects and dicts/lists
		:param schema: schema to use to dump 'data'
		:param template_string: text generated by end-users
		:param sub_templates: list of sub_templates [(<name>: <template_string>)]
		:return: rendered template
		"""

		# substitute sub template tag names with
		for tag_name, tag_template_str in sub_templates or []:
			template_string = template_string.replace("{%s}" % tag_name, tag_template_str)

		get_schema = lambda k: next((s for s in Smores.schemas if s.__name__.lower() == k.lower()), None)

		# parse end-user template (converts {user.addresses:3.name} to {{user.addresses[2].name}})
		# gives a 'slightly' less intimidating language syntax for the user to understand.
		jinja_template = to_jinja_template(template_string)

		# create the template object
		template = self.env.from_string(jinja_template)

		# create context for top-level template rendering
		# allows for {user.address} AND {address}

		context_dict = {}
		for k, v in data.items():
			schema = get_schema(k)
			if schema:
				s = schema()
				context_dict[k] = s.dump(v).data

		# render and prettify output
		raw = template.render(**context_dict)
		soup = bs(raw, "html.parser")
		return soup.prettify()

