from bs4 import BeautifulSoup

def loop_table_rows(iterable_tags, template_string):
	soup = BeautifulSoup(template_string, 'html.parser')
	table = soup.find('table')

	for tag, for_statement_params in iterable_tags.items():
		iterator, iterable = for_statement_params
		for_statement = "{% for " + iterator + " in " + iterable + " %}"
		td = table.find('td', string=tag)
		rows = []
		if td:
			tr = td.parent
			tr.insert_before(for_statement)
			while True:
				try:
					found = tr.find_next_sibling().find('td', string=tag).parent
					if found:
						rows.append(found)
						tr = found
				except Exception as e:
					break
			tr.insert_after("{% endfor %}")
	return str(soup)
