# Smores

This is an attempt at creating a user-facing templating system backed by Jinja2 and Marshmallow.  

The primary concept is that templates can be created for schemas.  As the template is parsed, we also walk the marshmallow schemas.  If a variable lands on a field, the string representation of the field is returned. If the variable lands on a schema itself, the return value of smores_template is rendered.****


