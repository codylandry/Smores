from marshmallow import Schema, fields
from sample_data import SAMPLE_DATA
from smores import render


# EXAMPLE Marshmallow Schemas
class Coordinates(Schema):
	lat = fields.Decimal()
	lng = fields.Decimal()

	@staticmethod
	def smores_template():
		return """
			<ul>
				Coordinates
				<li>lat: {{ 'lat' | get_data }}</li>
				<li>lng: {{ 'lng' | get_data }}</li>
			</ul>
			"""


class Address(Schema):
	street = fields.String()
	suite = fields.String()
	city = fields.String()
	zipcode = fields.String()
	geo = fields.Nested(Coordinates)

	@staticmethod
	def smores_template():
		return """
			<div>
				Address
				<div>street: {{ 'street' | get_data }}</div>
				<div>suite: {{ 'suite' | get_data }}</div>
				<div>city: {{ 'city' | get_data }}</div>
				<div>zipcode: {{ 'zipcode' | get_data }}</div>
				<div>
					{{ 'geo' | get_data }}
				</div>
			</div>
			"""


class Company(Schema):
	name = fields.String()
	catchPhrase = fields.String()
	bs = fields.String()

	@staticmethod
	def smores_template():
		return """
			<div>
				Company
				<div>name: {{ 'name' | get_data }}</div>
				<div>catchPhrase: {{ 'catchPhrase' | get_data }}</div>
				<div>bs: {{ 'bs' | get_data }}</div>
			</div>
			"""


class User(Schema):
	id = fields.Integer()
	name = fields.String()
	email = fields.Email()
	address = fields.Nested(Address)
	phone = fields.String()
	website = fields.String()
	company = fields.Nested(Company)

	@staticmethod
	def smores_template():
		return """
			<div>
				this is from the user schema
				{{ 'id' | get_data }}
				{{ 'name' | get_data }} 
				{{ 'email' | get_data }} 
				{{ 'address' | get_data }} 
				{{ 'phone' | get_data }} 
				{{ 'website' | get_data }} 
				{{ 'company.name' | get_data }} 
			</div>
			"""


template = """
	<div>
		<div>{{ 'user' | get_data }}</div>
		{{ 'address' | get_data }}
	</div>
"""

# simply provide the data, base schema and template string
print render(SAMPLE_DATA[0], User, template)

# outputs:
"""
	<div>
		<div>
			<div>
				this is from the user schema
				1
				Leanne Graham 
				Sincere@april.biz 

			<div>
				Address
				<div>street: Kulas Light</div>
				<div>suite: Apt. 556</div>
				<div>city: Gwenborough</div>
				<div>zipcode: 92998-3874</div>
				<div>

			<ul>
				Coordinates
				<li>lat: -37.3159</li>
				<li>lng: 81.1496</li>
			</ul>

				</div>
			</div>

				1-770-736-8031 x56442 
				hildegard.org 
				Romaguera-Crona 
			</div>
			</div>

			<div>
				Address
				<div>street: Kulas Light</div>
				<div>suite: Apt. 556</div>
				<div>city: Gwenborough</div>
				<div>zipcode: 92998-3874</div>
				<div>

			<ul>
				Coordinates
				<li>lat: -37.3159</li>
				<li>lng: 81.1496</li>
			</ul>

				</div>
			</div>

	</div>
"""
