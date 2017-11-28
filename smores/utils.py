import re
import inspect
from marshmallow import Schema

def get_module_schemas(module_):
	"""
	Returns list of all classes found in the module_

	# Arguments:
		module_ (module): where to find schemas

	# Returns:
		list: schemas found in module_
	"""
	is_schema = lambda obj: inspect.isclass(obj) and issubclass(obj, (Schema, ))
	schema_tuples = inspect.getmembers(module_, is_schema)
	return [s[1] for s in schema_tuples]

def loop_table_rows(iterable_tags, template_string):
	"""
	A template preprocessing function that enables a special way of
	iterating over values in a list of objects.  It searches for table cells
	with particular tags and wraps the table row (and subsequent rows if they also contain the tags) with
	a jinja for loop using the iterator, iterable tuple from 'iterable_tags'
	Example:

	# Arguments:
		iterable_tags (dict): mapping of
		template_string (str): jinja template string
	# Returns:
		string: transformed template string
	# Example:
	```python
	iterable_tags = {
		"mydogs.*": ("mydogs", "user.dogs")
	}

	input = '''
		<table>
			<tr>
				<td>{mydogs.name}</td>
			</tr>
			<tr>
				<td>{mydogs.weight}</td>
			</tr>
		</table>
	'''

	>>> smores.utils.loop_table_rows(input)
	<table>
		{% for mydogs in user.dogs %}
			<tr>
				<td>{mydogs.name}</td>
			</tr>
			<tr>
				<td>{mydogs.weight}</td>
			</tr>
		{% endfor %}
	</table>
	```
	"""
	from bs4 import BeautifulSoup
	soup = BeautifulSoup(template_string, 'html.parser')
	table = soup.find('table')

	for tag, for_statement_params in iterable_tags.items():
		iterator, iterable = for_statement_params
		for_statement = "{{% for {0} in {1} %}}".format(iterator, iterable)
		td = table.find('td', string=re.compile("{" + tag))
		rows = []
		if td:
			tr = td.parent
			tr.insert_before(for_statement)
			while True:
				try:
					found = tr.find_next_sibling().find('td', string=re.compile("{" + tag)).parent
					if found:
						rows.append(found)
						tr = found
				except Exception as e:
					break
			tr.insert_after("{% endfor %}")
	return str(soup)
