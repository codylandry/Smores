from marshmallow import Schema, fields
from smores import Smores

smores = Smores(fallback_value='!!!INVALID TAG!!!')

# EXAMPLE Marshmallow Schemas
@smores.schema
class Coordinates(Schema):
	lat = fields.Decimal()
	lng = fields.Decimal()
	_default_template = smores.TemplateString("""
		<div>
			{{lat}}, {{lng}}
		</div>
	""")

@smores.schema
class Address(Schema):
	street = fields.String()
	suite = fields.String()
	city = fields.String()
	zipcode = fields.String()
	geo = fields.Nested(Coordinates)
	_default_template = smores.TemplateString("""
		<div>
			<div>street: {street}</div>
			<div>suite: {suite}</div>
			<div>city: {city}</div>
			<div>zipcode: {zipcode}</div>
			<div>
				{geo.lat} {geo.lng}
			</div>
		</div>
	""", use_parser=True)

@smores.schema
class Company(Schema):
	name = fields.String()
	catchPhrase = fields.String()
	bs = fields.String()
	_default_template = smores.TemplateString("""
		<div>
			<div>name: {{ name }}</div>
			<div>catchPhrase: {{ catchPhrase }}</div>
			<div>bs: {{ bs }}</div>
		</div>
	""")

@smores.schema
class Dog(Schema):
	name = fields.String()
	_default_template = smores.TemplateString("""
		Name: {{ name }}
	""")

@smores.schema
class User(Schema):
	id = fields.Integer()
	name = fields.String()
	email = fields.Email()
	address = fields.Nested(Address)
	phone = fields.String()
	website = fields.String()
	company = fields.Nested(Company)
	dogs = fields.Nested(Dog, many=True)
	_default_template = smores.TemplateFile('templates/user.html')
	basic = smores.TemplateString("""
		<p>Name: {{name}}</p>
		<p>Email: {{email}}</p>
	""")

