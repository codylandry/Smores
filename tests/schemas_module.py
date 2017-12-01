from marshmallow import fields
from smores import TemplateFile, TemplateString, Schema, Nested

class Coordinates(Schema):
	lat = fields.Decimal()
	lng = fields.Decimal()


class Address(Schema):
	street = fields.String()
	suite = fields.String()
	city = fields.String()
	zipcode = fields.String()
	geo = Nested(Coordinates)
	_default_template = TemplateString("{{street}}---{{city}}---{{geo}}")


class Company(Schema):
	name = fields.String()
	catchPhrase = fields.String()
	bs = fields.String()
	_default_template = TemplateString("{{name}}---{{catchPhrase}}---{{bs}}")


class Dog(Schema):
	name = fields.String()
	dog =  Nested('self')
	_default_template = TemplateString("Name: {{ name }}")
	with_greeting = TemplateString('Hi, this is my dog {name}', use_parser=True)


class User(Schema):
	id = fields.Integer()
	name = fields.String()
	email = fields.Email()
	address = fields.Nested(Address)
	phone = fields.String()
	website = fields.String()
	company = Nested(Company)
	dogs = Nested('Dog', many=True)
	_default_template = TemplateString("""{{name}}---{{email}}""")
	basic = TemplateFile("tests/user_basic.html")
	long_template = TemplateString("{{name}}--{{phone}}--{{email}}--{{website}}--{{address.geo}}")
