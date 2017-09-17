from marshmallow import Schema, fields
from sample_data import SAMPLE_DATA
from smores import render, TemplateString, TemplateFile

# EXAMPLE Marshmallow Schemas
class Coordinates(Schema):
	lat = fields.Decimal()
	lng = fields.Decimal()
	_default_template = TemplateString("""
		<div>
			{{lat}}, {{lng}}
		</div>
	""")


class Address(Schema):
	street = fields.String()
	suite = fields.String()
	city = fields.String()
	zipcode = fields.String()
	geo = fields.Nested(Coordinates)
	_default_template = TemplateString("""
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


class Company(Schema):
	name = fields.String()
	catchPhrase = fields.String()
	bs = fields.String()
	_default_template = TemplateString("""
		<div>
			<div>name: {{ name }}</div>
			<div>catchPhrase: {{ catchPhrase }}</div>
			<div>bs: {{ bs }}</div>
		</div>
	""")

class Dog(Schema):
	name = fields.String()
	_default_template = TemplateString("""
		Name: {{ name }}
	""")

class User(Schema):
	id = fields.Integer()
	name = fields.String()
	email = fields.Email()
	address = fields.Nested(Address)
	phone = fields.String()
	website = fields.String()
	company = fields.Nested(Company)
	dogs = fields.Nested(Dog, many=True)
	# _default_template = TemplateFile('user.html')
	_default_template = TemplateString("""
		<div>
		    id: {{ id }}
		    name: {{ name }}
		    address: {{ address }}
		    company: {{company}}
		    dogs: {{ dogs }}
		</div>
	""")


template = """
	<div>
		<div>Dear {user.name}:</div>
		<p>
			Here's all the information we have about you!

			{user}
		</p>
		<p>Sincerely,</p>
		<p>{company.name} - {company.catchPhrase}</p>
		<em>{company.bs}</em>
	</div>
"""


print render(SAMPLE_DATA[0], User, template)
