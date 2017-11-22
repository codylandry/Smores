from marshmallow import Schema, fields
from parser import to_jinja_template, ATTR, delimitedList
from jinja2 import Environment
from collections import namedtuple

TagAutocompleteResponse = namedtuple('TagAutocompleteResponse', ('status', 'result'))


class TemplateString(fields.Field):
	# TemplateStrings never map to a particular value on the obj, but rather, the whole object
	_CHECK_ATTRIBUTE = False

	def __init__(self, template_string, env=None, use_parser=False, *args, **kwargs):
		"""
		Renders template_string using jinja w/o parser
		:param template_string: a jinja template
		:param env: jinja environment
		:param use_parser: flag for whether to use the smores parser
		"""
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


class TemplateFile(TemplateString):

	def __init__(self, template_path, env=None, use_parser=False, *args, **kwargs):
		"""
		Reads file at template_path and renders template using jinja w/o parser
		:param template_string: a jinja template
		:param env: jinja environment
		:param use_parser: flag for whether to use the smores parser
		"""
		# grab the template file
		with open(template_path, 'rb') as template_file:
			template_string = template_file.read()
		# pass it on to TemplateString
		super(TemplateFile, self).__init__(template_string, env=env, use_parser=use_parser, *args, **kwargs)


class RegisterTempSchemas(object):
	def __init__(self, smores_instance, schemas):
		"""
		A context manager for temporarily registering schemas with
		a smores instance
		:param schemas: single/list schema classes
		"""
		# if not isinstance(schemas, (list,)):
		# 	self.schemas = [schemas]
		# else:
		self.schemas = schemas
		self.smores_instance = smores_instance

	def __enter__(self):
		self.smores_instance.add_schemas(self.schemas)
		return self

	def __exit__(self, typ, val, traceback):
		self.smores_instance.remove_schemas(self.schemas)


class Smores(object):
	def __init__(self, default_template_name='_default_template'):
		"""
		Provides a method of defining a schema for string templates.  Presents a tag syntax
		easy enough for end users to use.
		:param default_template_name: The name you'd like to use for default schema templates
		"""
		self._DEFAULT_TEMPLATE = default_template_name

		# This jinja environment sets up a function to process variables into either serialized form or template
		self.env = Environment(finalize=self._process_jinja_variables())
		self.user_templates = {}
		self._registered_schemas = set([])

	def _process_jinja_variables(self):
		"""
		Does final processing of variables resolved by jinja.
		A dict means we have the result of a single schema dump.
		A list means we have the result of a dump of a list of schemas.
		For both cases, we attempt to get the _default_template of the schemas
		:param var: the value resolved by jinja for a variable
		:return: value to be rendered (string or template)
		"""
		_DEFAULT_TEMPLATE = self._DEFAULT_TEMPLATE
		def process(var):
			if isinstance(var, (list, )):
				# if var is a list return the _default_template for each item
				try:
					return "".join([v[_DEFAULT_TEMPLATE] for v in var])
				except:
					return ""
			if isinstance(var, (dict, )):
				# if var is a dict, then we must be returning a single schema, so try to get the _default_template
				try:
					return var[_DEFAULT_TEMPLATE]
				except:
					return ""
			# fallback to just returning the var as is (a plain field value)
			return var
		return process

	def temp_schemas(self, schemas):
		"""
		Returns a context manager that temporarily registers 'schemas'
		Useful for adding some schemas for a render call without polluting/conflicting
		with existing schemas
		:param schemas:  single schema or list of schemas
		:return: RegisterTempSchemas instance
		"""
		return RegisterTempSchemas(self, schemas)

	@property
	def schemas(self):
		return list(self._registered_schemas)

	def add_schemas(self, schemas):
		"""
		Registers schemas from instance
		:param schemas: single schema or list of schemas
		:return: None
		"""
		if not isinstance(schemas, (list,)):
			schemas = [schemas]
		else:
			schemas = schemas

		for schema in schemas:
			self._registered_schemas.add(schema)

	def remove_schemas(self, schemas):
		"""
		Unregisters schemas from instance
		:param schemas: single schema or list of schemas
		:return: None
		"""
		if not isinstance(schemas, (list,)):
			schemas = [schemas]
		else:
			schemas = schemas

		for schema in schemas:
			self._registered_schemas.remove(schema)

	def schema(self, schema):
		"""
		A decorator that registers a marshmallow schema
		:param schema: schema class
		:return: schema
		"""
		self.add_schemas(schema)
		return schema

	def autocomplete(self, fragment, only=None, exclude=None):
		"""
		Gets the available options for a given tag fragment
		:param base_schema: The schema the template was written for
		:param fragment: a tag fragment ex: user.addresses
		:param only: a list of schemas that should be included
		:param exclude: a list of schemas that should be excluded
		:return: a list of 'tab completion' results based on the tag fragment
		"""
		fragment = fragment.strip()
		sort_and_lower = lambda l: sorted([getattr(l, i) for i in l])

		# include/exclude root schemas from results
		allowed_root_schemas = self.schemas[:]
		if only:
			only = [s.lower() for s in only]
			allowed_root_schemas = [s for s in allowed_root_schemas if s.__name__.lower() in only]

		if exclude:
			exclude = [s.lower() for s in exclude]
			allowed_root_schemas = [s for s in allowed_root_schemas if s.__name__.lower() not in exclude]

		# return allowed schemas if fragment is blank
		if not fragment:
			return TagAutocompleteResponse("INVALID", sorted([s.__name__.lower() for s in allowed_root_schemas]))

		# parse fragment into tokens
		attrs = delimitedList(ATTR.setParseAction(lambda x: x[0]), delim='.')
		attrs = attrs.parseString(fragment)

		# attempt to get the root schema
		root_schema = next((s for s in allowed_root_schemas if s.__name__.lower() == attrs[0].lower()), None)
		if root_schema:
			current_node = root_schema()

		# otherwise get any schema starting with fragment
		elif len(attrs) == 1:
			result = [s.__name__.lower() for s in allowed_root_schemas
			          if s.__name__.lower().startswith(attrs[0].lower())]
			return TagAutocompleteResponse("INVALID", sorted(result))

		# otherwise, it's an invalid fragment
		else:
			return TagAutocompleteResponse("INVALID", [])

		get_fields = lambda n: map(lambda s: s.lower(), n.declared_fields.keys())
		current_node_field_names = get_fields(current_node)
		output = current_node_field_names
		attr = attrs[0].lower()
		for idx, attr in enumerate(attrs[1:]):
			is_last_attr = idx == len(attrs[1:]) - 1
			current_node_field_names = get_fields(current_node)

			# if valid attribute
			if attr.lower() in current_node_field_names:
				node = current_node.declared_fields[attr]

				# if nested field, get the associated schema
				if isinstance(node, fields.Nested):
					current_node = node.schema

					# if it's a many field and the last attr, return an option to index the array
					if is_last_attr and node.many == True:
						output = [':1']
						break

					# otherwise update the field names
					current_node_field_names = get_fields(current_node)
				else:
					current_node = None

			# if attr is an array index, just continue
			elif attr.startswith('['):
				continue

			# if the attr is only partially filled, return possible results
			else:
				current_node_field_names = [f for f in current_node_field_names if f.startswith(attr.lower())]

			output = current_node_field_names

		status = 'VALID'

		if isinstance(current_node, (Schema,)):
			if attr.lower() == current_node.__class__.__name__.lower():
				if '_default_template' not in output:
					status = "INVALID"

			elif attr not in get_fields(current_node):
				status = 'INVALID'

		else:
			output = []

		return TagAutocompleteResponse(status, sorted(output))

	def TemplateString(self, *args, **kwargs):
		"""
		Closure for instantiating the TemplateString field with the current env
		:return: TemplateString Instance
		"""
		return TemplateString(*args, env=self.env, **kwargs)

	def TemplateFile(self, *args, **kwargs):
		"""
		Closure for instantiating the TemplateFile field with the current env
		:return: TemplateFile Instance
		"""
		return TemplateFile(*args, env=self.env, **kwargs)

	def render(self, data, template_string, sub_templates=None, fallback_value=''):
		"""
		Recursively populates the 'template_string' with data gathered from dumping 'data' through the Marshmallow 'schema'.
		Variables are evaluated and will return the '_default_template' if one exists.  Prettifies end result.
		:param data: data to be dumped via the 'schema' (likely an ORM model instance) accepts both objects and dicts/lists
		:param schema: schema to use to dump 'data'
		:param template_string: text generated by end-users
		:param sub_templates: list of sub_templates [(<name>: <template_string>)]
		:return: rendered template
		"""

		assert isinstance(template_string, (basestring, )), 'template_string expected type string got %s' % type(template_string)

		# substitute sub template tag names with
		if sub_templates:
			for tag_name, tag_template_str in sub_templates.items():
				template_string = template_string.replace("{%s}" % tag_name, tag_template_str)

		get_schema = lambda k: next((s for s in self.schemas if s.__name__.lower() == k.lower()), None)

		# parse end-user template (converts {user.addresses:3.name} to {{user.addresses[2].name}})
		# gives a 'slightly' less intimidating language syntax for the user to understand.
		jinja_template = to_jinja_template(template_string, default=fallback_value)

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
		return raw

