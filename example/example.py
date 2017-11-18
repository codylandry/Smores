from sample_data import SAMPLE_DATA, EXTRA_DATA
from schemas import smores, fields, Schema, User

user_created_template = """
<h1>Smores</h1>
-------------------------
-------testing user sub templates
{my user template}

-------testing using the parser in backend templates (which support normal jinja syntax by default)
{user.address}
-------------------------
<section>
	<h4>Data is accessed by the user using the following syntax</h4>
	<p>Example:</p>
	<p>{user.address.street}</p>
</section>

<section>
	<h4>Provide templates as attributes</h4>
	<p>Beyond _default_template, you can provide templates exposed as attributes:</p>
	<p>{user.basic}</p>
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
	<p>{user.dogs:1}</p>
	<p>Just as with any other variable, if the array specifies a schema, the _default_template for that schema will be rendered.  If you specify a field, that field result will be rendered.</p>
	<p>{user.dogs:2.name}</p>
	<p>If you specify the list with no index, the _default_template will be returned for each item in the list</p>
	<p>{user.dogs}</p>
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

user_sub_templates = [
	('my user template', "{user.name}: {user.id}")
]

print smores.render(dict(user=SAMPLE_DATA[0], company=SAMPLE_DATA[0]['company']), user_created_template, sub_templates=user_sub_templates)

print smores.tag_autocomplete('address')


# showing how we can create an impromptu schema and provide extra data for special situations
test = """
{user.address.geo}
{event.tech.name}
{event.tag_from}
"""
@smores.schema
class Event(Schema):
	tech = fields.Nested(User)
	tag_to = fields.String()
	tag_from = fields.String()

print smores.render(dict(user=SAMPLE_DATA[0], event=EXTRA_DATA), test)
