<h1 id="smores.smores.TemplateString">TemplateString</h1>

```python
TemplateString(self, template_string, use_parser=False, *args, **kwargs)
```

Renders template_string using jinja w/o parser

__Arguments:__

	template_string (string): a jinja template
	env (Environment): jinja environment
	use_parser (bool): flag for whether to use the smores parser

<h1 id="smores.smores.TemplateFile">TemplateFile</h1>

```python
TemplateFile(self, template_path, use_parser=False, *args, **kwargs)
```

Reads file at template_path and renders template using jinja w/o parser

__Arguments:__

	template_string (string): a jinja template
	env (Environment): jinja environment
	use_parser (bool): flag for whether to use the smores parser

