<h1 id="smores.utils">smores.utils</h1>


<h2 id="smores.utils.get_module_schemas">get_module_schemas</h2>

```python
get_module_schemas(module_)
```

Returns list of all classes found in the module_

__Arguments:__

	module_ (module): where to find schemas

__Returns:__

	list: schemas found in module_

<h2 id="smores.utils.loop_table_rows">loop_table_rows</h2>

```python
loop_table_rows(iterable_tags, template_string)
```

A template preprocessing function that enables a special way of
iterating over values in a list of objects.  It searches for table cells
with particular tags and wraps the table row (and subsequent rows if they also contain the tags) with
a jinja for loop using the iterator, iterable tuple from 'iterable_tags'
Example:

__Arguments:__

	iterable_tags (dict): mapping of
	template_string (str): jinja template string
__Returns:__

	string: transformed template string
__Example:__

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

