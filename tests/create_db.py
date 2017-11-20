from pony.orm import *
from sample_data import users
from smores import Smores
from tests.sample_data import register_schemas
db = Database()

class User(db.Entity):
	id = PrimaryKey(int, auto=True)
	name = Required(str)
	username = Required(str)
	email = Required(str)
	phone = Required(str)
	website = Required(str)
	address = Optional('Address')
	dogs = Set('Dog')
	company = Optional('Company')

class Address(db.Entity):
	street = Required(str)
	suite = Required(str)
	city = Required(str)
	zipcode = Required(str)
	user = Required(User)
	geo = Optional('Geo')

class Geo(db.Entity):
	lat = Required(str)
	lng = Required(str)
	address = Required(Address)

class Company(db.Entity):
	name = Required(str)
	catchPhrase = Required(str)
	bs = Required(str)
	user = Required(User)

class Dog(db.Entity):
	name = Required(str)
	user = Required(User)

db.bind(provider='sqlite', filename=':memory:')
db.generate_mapping(create_tables=True)

with db_session:
	for user in users:
		db_user = User(**{k: v for k, v in user.items() if k not in ['address', 'company', 'dogs']})
		db_address = Address(user=db_user, **{k: v for k, v in user['address'].items() if k != 'geo'})
		db_geo = Geo(address=db_address, **user['address']['geo'])
		db_company = Company(user=db_user, **user['company'])
		for dog in user.get('dogs', []):
			db_dog = Dog(user=db_user, name=dog['name'])

	smores = Smores()
	register_schemas(smores)
