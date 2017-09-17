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
	_default_template = TemplateFile('templates/user.html')

template = """
<h1>Smores</h1>

<section>
	<h4>Data is accessed by the user using the following syntax</h4>
	<p>Example:</p>
	<p>{user.address.street}</p>
	<p>Users can optionally specify the 'root' name, in this case 'user'.  This returns the same result.</p>
	<p>{address.street}</p>
</section>

<section>
	<h4>Fields vs. Schema Results</h4>
	<p>When a field is accessed, the result of Marshmallow's serialize method for that type of field is returned, but when the result ends at a schema level, Smores looks for a _default_template of type TemplateString or TemplateFile.  The _default_template is rendered in place.</p>
	<p>Example: </p>
	<p>{user}</p>
	<p>{user.address.geo}</p>
</section>

<section>
	<h4>Arrays</h4>
	<p>Array items are specified using ':index'. For example:</p>
	<p>{dogs:1}</p>
	<p>Just as with any other variable, if the array specifies a schema, the _default_template for that schema will be rendered.  If you specify a field, that field result will be rendered.</p>
	<p>{dogs:2.name}</p>
	<p>If you specify the list with no index, the _default_template will be returned for each item in the list</p>
	<p>{dogs}</p>
</section>

<section>
	<h4>Behavior</h4>
	<p>Most all of Marshmallow and jinja's power are conserved, but the following needs to be done to make it available to the user:</p>
	<ul>
		<li>Support 'dump_to' in marshmallow fields.</li>
		<li>Support jinja filters in user templates.</li>
		<li>Make Pre-parsing optional and pluggable.</li>
		<li>Make post-processing (BeautifulSoup.prettify) optional and pluggable. (Add support to minify?)</li>
		<li>Allow ability to extend the jinja Environment</li>
	</ul>
</section>

<h3>Note: Some of these limitations only exists because we aren't exposing bracket notation for array indexes to users. If we use bracket notation and "{{'{{'}} {{'}}'}}", we can effectively give the user the power of jinja outright.</h3>
"""


print render(SAMPLE_DATA[0], User, template)

# outputs ->
"""
<div>
 <div>
  Dear Leanne Graham:
 </div>
 <p>
  Here's all the information we have about you!
  <div>
   id: 1
		    name: Leanne Graham
		    address:
   <div>
    <div>
     street: Kulas Light
    </div>
    <div>
     suite: Apt. 556
    </div>
    <div>
     city: Gwenborough
    </div>
    <div>
     zipcode: 92998-3874
    </div>
    <div>
     <div>
      -37.3159, 81.1496
     </div>
    </div>
   </div>
   company:
   <div>
    <div>
     name: Romaguera-Crona
    </div>
    <div>
     catchPhrase: Multi-layered client-server neural-net
    </div>
    <div>
     bs: harness real-time e-markets
    </div>
   </div>
   dogs: 
		Name: Rufus
	
		Name: Snoopy
	
		Name: Scratch
	
		Name: Spot
  </div>
 </p>
 <p>
  Sincerely,
 </p>
 <p>
  Romaguera-Crona -
 </p>
 <em>
  harness real-time e-markets
 </em>
</div>
"""
