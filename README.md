# Smores

This is an attempt at creating a user-facing templating system backed by Jinja2 and Marshmallow.  

The primary concept is that templates can be created for schemas.  As the template is parsed, we also walk the marshmallow schemas.  If a variable lands on a field, the string representation of the field is returned. If the variable lands on a schema itself, the return value of smores_template is rendered.****


###TODO

- add support for arrays
- add support for multiple templates per schema
- deal with marshmallow 'load_from' fields
- add a way to customize user facing syntax (delimiters for dot operator and list indexing)
- add ability to blacklist fields from being included in templates
- add ability to specify a template for (non-Nested) fields
