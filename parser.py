from pyparsing import Literal, Word, alphanums, Optional, Group, delimitedList, ParserElement

def convert_integers(tokens):
	return int(tokens[0])

def _bracketize(tokens):
	return '[' + tokens[0].index + ']'

def _lowerize(tokens):
	return tokens[0].lower()

def _combine_path(tokens):
	nodes = map(''.join, tokens)
	path = '.'.join(nodes)
	return path
	# return " '{path}' | smores_data ".format(path=path)

def _get_jinja_tag(tokens):
	return ''.join(tokens[0])

def _adjust_indexes(tokens):
	return str(int(tokens[0]) - 1)

def to_jinja_template(template_string):
	ParserElement.setDefaultWhitespaceChars('')
	START = Literal('{').setParseAction(lambda: '{{')
	END = Literal('}').setParseAction(lambda: '}}')
	integer = Word('0123456789').setParseAction(_adjust_indexes).setResultsName('index')
	LIST_INDEX = Group(Literal(':').suppress() + integer).setParseAction(_bracketize)
	ATTR_NAME = Word(alphanums + '_').setParseAction(_lowerize)
	ATTR = Group(ATTR_NAME + Optional(LIST_INDEX))
	PATH = delimitedList(ATTR, delim='.').setParseAction(_combine_path).setWhitespaceChars(' ')
	TAG = Group(START + PATH + END).setParseAction(_get_jinja_tag).setWhitespaceChars(' ')

	temp = TAG.transformString(template_string)
	# temp = PATH.transformString(temp)
	return temp
