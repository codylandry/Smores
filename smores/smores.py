from marshmallow import fields
from marshmallow.schema import SchemaMeta, BaseSchema
from marshmallow.base import SchemaABC
from marshmallow.compat import with_metaclass
from .utils import get_module_schemas
from parser import to_jinja_template, ATTR, delimitedList, de_bracketize
from jinja2 import Environment
from collections import namedtuple
from inspect import isfunction
import class_registry
from contextlib import contextmanager
import re

AutocompleteResponse = namedtuple('AutocompleteResponse', ('tagStatus', 'options', 'validFragment'))


class TemplateString(fields.Field):
	"""
	Renders template_string using jinja w/o parser

	# Arguments:
		template_string (string): a jinja template
		env (Environment): jinja environment
		use_parser (bool): flag for whether to use the smores parser
	"""
	_CHECK_ATTRIBUTE = False

	def __init__(self, template_string, use_parser=False, *args, **kwargs):
		super(TemplateString, self).__init__(*args, **kwargs)

		# the template string to be rendered
		if use_parser:
			template_string = to_jinja_template(template_string)
		self.template_string = template_string

		# TemplateStrings do not get 'loaded' by marshmallow
		self.dump_only = True

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
		context = schema(exclude=template_fields, context=self.context).dump(obj).data  # TODO - cache this

		# return rendered template
		env = self.context['env']

		template = env.from_string(self.template_string)
		return template.render(**context)


class TemplateFile(TemplateString):
	"""
	Reads file at template_path and renders template using jinja w/o parser

	# Arguments:
		template_string (string): a jinja template
		env (Environment): jinja environment
		use_parser (bool): flag for whether to use the smores parser
	"""

	def __init__(self, template_path, use_parser=False, *args, **kwargs):
		# grab the template file
		with open(template_path, 'rb') as template_file:
			template_string = template_file.read()
		# pass it on to TemplateString
		super(TemplateFile, self).__init__(template_string, use_parser=use_parser, *args, **kwargs)


class SmoresEnvironment(Environment):
	def getattr(self, obj, attribute):
		"""Get an item or attribute of an object but prefer the attribute.
		Unlike :meth:`getitem` the attribute *must* be a bytestring.
		"""
		try:
			data = {k.lower(): v for k, v in obj.items()}
			return data[attribute.lower()]
		except:
			return self.undefined(obj=obj, name=attribute)


class SmoresSchemaMeta(SchemaMeta):
	def __init__(self, name, bases, attrs):
		super(SchemaMeta, self).__init__(name, bases, attrs)
		if name:
			class_registry.register(name, self)
		self._resolve_processors()


class Schema(with_metaclass(SmoresSchemaMeta, BaseSchema)):
	__doc__ = BaseSchema.__doc__


_RECURSIVE_NESTED = 'self'


class Nested(fields.Nested):
	@property
	def schema(self):
		"""The nested Schema object.
		.. versionchanged:: 1.0.0
			Renamed from `serializer` to `schema`
		"""
		if not self.__schema:
			# Ensure that only parameter is a tuple
			if isinstance(self.only, basestring):
				only = (self.only,)
			else:
				only = self.only

			# Inherit context from parent.
			context = getattr(self.parent, 'context', {})
			if isinstance(self.nested, type) and \
					issubclass(self.nested, SchemaABC):
				self.__schema = self.nested(many=self.many,
				                            only=only, exclude=self.exclude, context=context,
				                            load_only=self._nested_normalized_option('load_only'),
				                            dump_only=self._nested_normalized_option('dump_only'))
			elif isinstance(self.nested, basestring):
				if self.nested == _RECURSIVE_NESTED:
					parent_class = self.parent.__class__
					self.__schema = parent_class(many=self.many, only=only,
					                             exclude=self.exclude, context=context,
					                             load_only=self._nested_normalized_option('load_only'),
					                             dump_only=self._nested_normalized_option('dump_only'))
				else:
					schema_class = class_registry.get_class(self.nested)
					self.__schema = schema_class(many=self.many,
					                             only=only, exclude=self.exclude, context=context,
					                             load_only=self._nested_normalized_option('load_only'),
					                             dump_only=self._nested_normalized_option('dump_only'))
			else:
				raise ValueError('Nested fields must be passed a '
				                 'Schema, not {0}.'.format(self.nested.__class__))
			self.__schema.ordered = getattr(self.parent, 'ordered', False)
		return self.__schema


class Smores(object):
	"""
	Provides a method of defining a schema for string templates.  Presents a tag syntax
	easy enough for end users to use.

	# Arguments:
		default_template_name (str): The name you'd like to use for default schema templates
	"""

	def __init__(self, default_template_name='_default_template'):
		self._DEFAULT_TEMPLATE = default_template_name

		# This jinja environment sets up a function to process variables into either serialized form or template
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
			if isinstance(var, (list,)):
				# if var is a list return the _default_template for each item
				try:
					return "".join([v[_DEFAULT_TEMPLATE] for v in var])
				except:
					return ""
			if isinstance(var, (dict,)):
				# if var is a dict, then we must be returning a single schema, so try to get the _default_template
				try:
					return var[_DEFAULT_TEMPLATE]
				except:
					return ""
			# fallback to just returning the var as is (a plain field value)
			return var

		return process

	@contextmanager
	def with_schemas(self, schemas):
		"""
		Context manager that registers schemas temporarily

		# Arguments:
			schemas (list|Schema):  single schema or list of schemas

		# Example:
			class Event(Schema):
				time = fields.DateTime()
				description = fields.String()

			with smores.with_schemas(Event):
				# Event schema available here
				smores.render(someDate, someTemplate)

			# Event schema is removed on exit
		"""
		self.add_schemas(schemas)
		yield
		self.remove_schemas(schemas)

	@property
	def schemas(self):
		"""
		Property that returns a list of registered schemas

		# Returns:
			list: Currently registered schemas
		"""
		return list(self._registered_schemas)

	def add_module_schemas(self, module_):
		"""
		Adds all Schema classes found in module_

		# Arguments:
			module_ (module): Registers schema classes from this module
	    """
		self.add_schemas(get_module_schemas(module_))

	def add_schemas(self, schemas):
		"""
		Registers schema(s)

		# Arguments:
			schemas (Schema|list): schemas to register
		"""
		if not isinstance(schemas, (list,)):
			schemas = [schemas]
		else:
			schemas = schemas

		for schema in schemas:
			self._registered_schemas.add(schema)

	def remove_schemas(self, schemas):
		"""
		Unregisters schema(s)

		# Arguments:
			schemas (Schema|list): schemas to unregister
		"""
		if not isinstance(schemas, (list,)):
			schemas = [schemas]
		else:
			schemas = schemas

		for schema in schemas:
			self._registered_schemas.remove(schema)

	def schema(self, schema):
		"""
		A class decorator that registers a marshmallow schema

		# Example:
			smores = Smores()

			@smores.schema
			class User(Schema):
				name = fields.String()
				email = fields.Email()
		"""
		self.add_schemas(schema)
		return schema

	@staticmethod
	def _filter_schemas(schemas, only=None, exclude=None):
		schemas = schemas[:]

		if only:
			only = [s.lower() for s in only]
			schemas = [s for s in schemas if s.__name__.lower() in only]

		if exclude:
			exclude = [s.lower() for s in exclude]
			schemas = [s for s in schemas if s.__name__.lower() not in exclude]

		return schemas



	def get_tags(self, only=None, exclude=None):
		"""
		Retrieve the complete list of tags

		# Arguments
			only (list): only use these root schema names
			exclude (list): exclude these root schema names

		# Returns:
			list: possible tags
		"""
		output = []
		def build_tags(name, schema, ignore_fields=None):
			ret = []
			for field_name, field in schema._declared_fields.items():


				if isinstance(field, Nested):
					if field_name in (ignore_fields or []):
						continue

					full_path = name + "." + field_name

					if field.many:
						full_path += ":1"

					check_re = re.compile(full_path + r"\.([a-zA-Z0-9_]*)($|\.)")
					recursive_fields = [field_name] if field.nested == _RECURSIVE_NESTED else None
					field_schema = field.schema if field.nested != _RECURSIVE_NESTED else schema
					res = [(re.search(check_re, p).group(1), p) for p in
					       build_tags(full_path, field_schema, ignore_fields=recursive_fields)]

					res = [v for k, v in res
					       if not field.only or k in field.only
					       and not field.exclude or k not in field.exclude]
					ret.extend(res)

				elif self._DEFAULT_TEMPLATE != field_name:
					ret.append(".".join([name, field_name]))
			return ret

		schemas = self._filter_schemas(self.schemas, only=only, exclude=exclude)
		for s in schemas:
			if self._DEFAULT_TEMPLATE in s._declared_fields:
				output.append(s.__name__)
			output.extend(build_tags(s.__name__, s))

		output = sorted([p.lower() for p in output])

		return output


	def autocomplete(self, fragment, only=None, exclude=None):
		"""
		Evaluates a tag fragment, returns a named tuple with the status of the fragment
		as it is, and possible options that could be used to expand/add to the fragment.

		# Arguments:
			fragment (string): a tag fragment ex: user.addresses
			only (list): a list of schemas that should be included
			exclude (list): a list of schemas that should be excluded

		# Returns:
			AutocompleteResponse: NamedTuple with both the status of the current tag fragment as well as possible options

		# Example:
		    >>> smores.autocomplete("")
		    AutocompleteResponse(tagStatus='INVALID', options=['address', 'coordinates', 'user'])

		    >>> smores.autocomplete('user')
		    AutocompleteResponse(tagStatus='VALID', options=['_default_template', 'address', 'email', 'id', 'name'])

		    >>> smores.autocomplete('us')
		    AutocompleteResponse(tagStatus='INVALID', options=['user'])

		    >>> smores.autocomplete("user.address.coordinates")
		    AutocompleteResponse(tagStatus='VALID', options=['_default_template', 'lat', 'lng'])
		"""
		valid_fragment = ""
		fragment = fragment.strip()
		valid = True

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
			return AutocompleteResponse("INVALID", sorted([s.__name__.lower() for s in allowed_root_schemas]),
			                            valid_fragment)

		# parse fragment into tokens
		attrs = delimitedList(ATTR.setParseAction(lambda x: x[0]), delim='.')
		attrs = attrs.parseString(fragment)

		# attempt to get the root schema
		root_schema = next((s for s in allowed_root_schemas if s.__name__.lower() == attrs[0].lower()), None)
		if root_schema:
			valid_fragment += attrs[0].lower()
			current_node = root_schema()

		# otherwise get any schema starting with fragment
		elif len(attrs) == 1:
			result = [s.__name__.lower() for s in allowed_root_schemas
			          if s.__name__.lower().startswith(attrs[0].lower())]
			return AutocompleteResponse("INVALID", sorted(result), valid_fragment)

		# otherwise, it's an invalid fragment
		else:
			return AutocompleteResponse("INVALID", [], valid_fragment)

		get_fields = lambda n: map(lambda s: s.lower(), n.declared_fields.keys())
		current_node_field_names = get_fields(current_node)
		output = current_node_field_names
		attr = attrs[0]

		for idx, attr in enumerate(attrs[1:]):
			is_last_attr = idx == len(attrs[1:]) - 1
			try:
				current_node_field_names = get_fields(current_node)
			except:
				current_node_field_names = []

			# if valid attribute
			if attr.lower() in current_node_field_names:
				fields = {k.lower(): v for k, v in current_node.declared_fields.items()}
				node = fields[attr.lower()]

				# if nested field, get the associated schema
				if isinstance(node, Nested):
					current_node = node.schema

					# if it's a many field and the last attr, return an option to index the array
					if is_last_attr and node.many == True:
						output = [':1']
						break

					# otherwise update the field names
					current_node_field_names = get_fields(current_node)
					output = current_node_field_names
				else:
					current_node = None

				valid_fragment += "." + attr.lower()
				continue

			# if attr is an array index, just continue
			elif attr.startswith('['):
				valid_fragment += de_bracketize(attr)
				continue

			# if the attr is only partially filled, return possible results
			else:
				valid = False
				current_node_field_names = [f for f in current_node_field_names if f.startswith(attr.lower())]

				output = current_node_field_names
				break

		status = 'VALID'

		if isinstance(current_node, (Schema,)):
			if attr.lower() == current_node.__class__.__name__.lower():
				if '_default_template' not in output:
					status = "INVALID"

			elif attr not in get_fields(current_node):
				status = 'INVALID'

		else:
			output = []

		status = status if valid else "INVALID"

		return AutocompleteResponse(status, sorted(output), valid_fragment)

	def render(self, data, template_string, sub_templates=None, fallback_value='', pre_process=None):
		"""
		Recursively populates the 'template_string' with data gathered from dumping 'data' through the Marshmallow 'schema'.
		Variables are evaluated and will return the '_default_template' if one exists.  Prettifies end result.

		# Arguments
			data (dict): data to be dumped via the 'schema' (likely an ORM model instance) accepts both objects and dicts/lists
			template_string (str): text generated by end-users
			sub_templates (dict): mapping of subtemplate tag to expanded sub template string
			fallback_value (str|function|None): either string or function returning a string to serve as default value for tag attrs that cannot be resolved
			pre_process (function): function that modifies the parsed version of the template

		# Returns:
			string: rendered template
		"""
		assert not sub_templates or isinstance(sub_templates, (dict,)), \
			'sub_templates must be a dict of <tag>: <subtemplate>'
		assert not pre_process or isfunction(pre_process), \
			'pre_process must be a function'
		assert isinstance(template_string, (basestring,)), \
			'template_string expected type string got %s' % type(template_string)

		# substitute sub template tag names with
		if sub_templates:
			for tag_name, tag_template_str in sub_templates.items():
				template_string = template_string.replace("{%s}" % tag_name, tag_template_str)

		# parse end-user template (converts {user.addresses:3.name} to {{user.addresses[2].name}})
		# gives a 'slightly' less intimidating language syntax for the user to understand.
		jinja_template = to_jinja_template(template_string, default=fallback_value)

		# allows processing of template after parsing but before rendering
		if pre_process:
			jinja_template = pre_process(jinja_template)

		# create the template object
		env = SmoresEnvironment(finalize=self._process_jinja_variables())
		template = env.from_string(jinja_template)

		get_schema = lambda k: next((s for s in self.schemas if s.__name__.lower() == k.lower()), None)
		context_dict = {}
		for k, v in data.items():
			schema = get_schema(k)
			if schema:
				s = schema(context=dict(env=env))
				context_dict[k.lower()] = s.dump(v).data

		return template.render(**context_dict)
