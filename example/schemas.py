from marshmallow import Schema, fields
from smores import Smores

smores = Smores()

# EXAMPLE Marshmallow Schemas
@Smores.schema
class Coordinates(Schema):
	lat = fields.Decimal()
	lng = fields.Decimal()
	_default_template = smores.TemplateString("""
		<div>
			{{lat}}, {{lng}}
		</div>
	""")

@Smores.schema
class Address(Schema):
	street = fields.String()
	suite = fields.String()
	city = fields.String()
	zipcode = fields.String()
	geo = fields.Nested(Coordinates)
	_default_template = smores.TemplateString("""
		<div>
			<div>street: {{ street }}</div>
			<div>suite: {{ suite }}</div>
			<div>city: {{ city }}</div>
			<div>zipcode: {{ zipcode }}</div>
			<div>
				{{ geo }}
			</div>
		</div>
	""")

@Smores.schema
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

@Smores.schema
class Dog(Schema):
	name = fields.String()
	_default_template = smores.TemplateString("""
		Name: {{ name }}
	""")

@Smores.schema
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
