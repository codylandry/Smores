from pyparsing import Literal, Word, alphanums, Optional, Group, delimitedList, ParserElement, originalTextFor, NotAny, FollowedBy, OnlyOnce
import inspect


def _bracketize(tokens):
	return '[' + tokens[0].index + ']'

def _colonize(tokens):
	return ":" + str(int(tokens[0][0]) + 1)

def _lowerize(tokens):
	return tokens[0].lower()


def _combine_path(tokens):
	nodes = map(''.join, tokens)
	path = '.'.join(nodes)
	return path

def get_original_tag(tag):
	_START = Literal('{{').setParseAction(lambda: '{')
	_END = Literal('}}').setParseAction(lambda: '}')
	_ATTR_NAME = Word(alphanums + '_').setParseAction(_lowerize)
	_LIST_INDEX = Group(Literal('[').suppress() + integer + Literal(']').suppress()).setParseAction(_colonize)
	_ATTR = Group(_ATTR_NAME + Optional(_LIST_INDEX))
	_PATH = delimitedList(_ATTR, delim='.').setParseAction(_combine_path).setWhitespaceChars(' ')
	_BASE_TAG = Group(_START + _PATH + _END)

	result = _BASE_TAG.transformString(tag)
	return result

def _get_jinja_tag(default):
	def wrapped(tokens):
		tokens = tokens[0]
		output = "".join(tokens)

		original_tag = get_original_tag(output)
		if not default:
			_default = ''
		elif isinstance(default, (basestring, )):
			_default = default
		elif inspect.isfunction(default):
			_default = default(original_tag)

		tokens.insert(2, " | default('%s')" % _default)
		output = "".join(tokens)
		return output
	return wrapped


def _adjust_indexes(tokens):
	# make indexes '1-based'
	return str(int(tokens[0]) - 1)


JINJA_TOKENS = Literal('%') | Literal('#') | Literal('{')

ParserElement.setDefaultWhitespaceChars('')
START = Literal('{').setParseAction(lambda: '{{')
END = Literal('}').setParseAction(lambda: '}}')
integer = Word('0123456789').setParseAction(_adjust_indexes).setResultsName('index')
LIST_INDEX = Group(Literal(':').suppress() + integer).setParseAction(_bracketize)
ATTR_NAME = Word(alphanums + '_').setParseAction(_lowerize)
ATTR = Group(ATTR_NAME + Optional(LIST_INDEX))
PATH = delimitedList(ATTR, delim='.').setParseAction(_combine_path).setWhitespaceChars(' ')
BASE_TAG = Group(START + PATH + END)

def to_jinja_template(template_string, default=""):
	"""
	This function allows us to expose a 'slightly' less intimidating syntax to the user.  It accepts a 'user-generated'
	template with variables referenced using the following syntax:

		{root.attribute:list_index.deeper_attribute}

	This gets parsed and converted to generate a valid jinja template tag:

		{{root.attribute[list_index].deeper_attribute}}

	:param template_string: a user-generated template
	:param default: a string value to use when jinja can't resolve the tag USE "ORIGINAL" to place the tag
					back in the template
	:return: a jinja version of the template
	"""

	TAG = BASE_TAG.setParseAction(_get_jinja_tag(default)).setWhitespaceChars(' ')

	temp = TAG.transformString(template_string)
	# temp = PATH.transformString(temp)
	return temp
