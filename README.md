# Smores

Smores allows you to specify a schema for user facing template features.  It leverages marshmallow (hence 'smores') to
populate and transform data that is then rendered via jinja.  It has a parser that presents a more friendly syntax to 
users (ex. {user.addresses:1.street}).  It also includes an autocomplete method that gives you intellisense style 
options given a tag fragment.  

Smores provides two Marshmallow field types called TemplateString and TemplateFile.  Templates defined in these fields
are scoped to that schema and it's descendants.  Each schema can have a _default_template that, if defined, will what
is inserted if the associated tag ends with that schema.  For example: typing {user.address} will render the _default_template
for the Address schema.  You can define other template attributes as well.  For example, see the 'google_link' attribute
of the Address schema below.  Typing {user.address.google_link} will populate and insert that link.  

smores.tag_autocomplete is a method where you can provide a tag 'fragment' and it will return the possible options below that.
For example:
    
    for the schemas below

    smores.tag_autocomplete("") returns ['user', 'address', 'coordinates']
    smores.tag_autocomplete("user") returns ['id', 'name', 'email', 'address', '_default_template']
    smores.tag_autocomplete("user.address.geo") returns ['lat', 'lng', '_default_template']
    
    Receiving '_default_template' or no results means that the current tag fragment is valid but _default_template
    shouldn't be appended to the tag in the ui.


```python
from smores import Smores
from marshmallow import Schema, fields

# instantiate a smores instance
smores = Smores()

# smores.schema registers the schema with the instance
@smores.schema
class Coordinates(Schema):
    lat = fields.Decimal()
    lng = fields.Decimal()
    _default_template = smores.TemplateString("{{lat}},{{lng}}")

@smores.schema
class Address(Schema):
    street = fields.String()
    suite = fields.String()
    city = fields.String()
    state = fields.String()
    zipcode = fields.String()
    coordinates = fields.Nested(Coordinates)
    google_link = smores.TemplateString('<a href="https://maps.google.com/?ll={{coordinates}}">View Map</a>')
    _default_template = smores.TemplateString("""
        <div>{{<a href="https://maps.google.com/?ll={{coordinates}}">View Map</a>}}</div>
        <div>{{street}} -- {{suite}}</div>
        <div>{{city}}, {{state}} {{zipcode}}</div>
    """)

@smores.schema
class User(Schema):
    id = fields.Integer()
    name = fields.String()
    email = fields.Email()
    address = fields.Nested(Address)
    _default_template = smores.TemplateString("""
        <div>{{name}}</div>
        <div>E: {{email}}</div>
        <div>{{address}}</div>
    """)


# provide data to the render function
data = {
    "user": {
        "id": 1,
        "name": "Leanne Graham",
        "username": "Bret",
        "email": "Sincere@april.biz",
        "phone": "1-770-736-8031 x56442",
        "address": {
            "street": "Kulas Light",
            "suite": "Apt. 556",
            "city": "Gwenborough",
            "state": "MD",
            "zipcode": "92998-3874",
            "coordinates": {
                "lat": "36.065934",
				"lng": "-79.791414"
            }
        },
    }
}

# provide user created template
user_template = """
    <h3>Hi, {user.name}!</h3>
    <p>Your Info:</p>
    {user}
"""

# render the output
print smores.render(data, user_template)

# output -->
# <h3>Hi, Leanne Graham!</h3>
# <p>Your Info:</p>
# 
# <div>Leanne Graham</div>
# <div>E: Sincere@april.biz</div>
# <div>
#     <div><a href="https://www.google.com/maps.google.com/?ll=-37.3159,81.1496">View Map</a></div>
#     <div>Kulas Light -- Apt. 556</div>
#     <div>Gwenborough, MD 92998-3874</div>
# </div>

```

### TODOS

- [ ] Publish on PyPI
- [ ] Add test that use model classes from an orm (probably use Pony and sqlite)
- [ ] Add CircleCi integration for PR's
- [ ] Improve Documentation
- [ ] Add option to not use parser
