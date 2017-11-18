from smores import Smores
from sample_data import users
from marshmallow import fields, Schema

def test_simple_template():
	smores = Smores()

	@smores.schema
	class User(Schema):
		id = fields.Integer()
		name = fields.String()
		email = fields.Email()
		phone = fields.String()
		website = fields.String()
		_default_template = smores.TemplateString("<p>Name: {{name}}</p><p>Email: {{email}}</p>")

	result = smores.render(dict(user=users[0]), "{user}")
	assert result == "<p>Name: Leanne Graham</p><p>Email: Sincere@april.biz</p>"
