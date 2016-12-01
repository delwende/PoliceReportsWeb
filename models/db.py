# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

## app configuration made easy. Look inside private/appconfig.ini
from gluon.contrib.appconfig import AppConfig
## once in production, remove reload=True to gain full speed
myconf = AppConfig(reload=True)


if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL(myconf.take('db.uri'), pool_size=myconf.take('db.pool_size', cast=int), check_reserved=['all'])
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore+ndb')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## choose a style for forms
response.formstyle = myconf.take('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.take('forms.separator')


## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'
## (optional) static assets folder versioning
# response.static_version = '0.0.0'
#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Service, PluginManager

auth = Auth(db)
service = Service()
plugins = PluginManager()

auth.settings.extra_fields['auth_user'] = [
        Field('grade', 'string'),
        Field('dependency', 'string'),
        Field('role', 'string'),
        Field('seconded_by', 'string'),
        ]

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
#mail.settings.server = 'logging' if request.is_local else myconf.take('smtp.server')
mail.settings.server = myconf.take('smtp.server')
mail.settings.sender = myconf.take('smtp.sender')
mail.settings.login = myconf.take('smtp.login')

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True
auth.settings.actions_disabled.append('register')
auth.settings.actions_disabled.append('request_reset_password')


db.define_table('citizen',
    Field('name', 'string', label=T('Name')),
    Field('last_name', 'string', label=T('Last name')),
    Field('ssn', 'string', unique=True, label=T('Ssn')),
    Field('nationality', 'string', label=T('Nationality')),
    Field('birth_date', 'date', label=T('Birth Date')),
    Field('address', 'string', label=T('Address')),
    Field('phone', 'string', label=T('Phone')),
    Field('email', 'string', unique=True,requires=[IS_EMAIL()]),
    Field('occupation', 'string', label=T('Occupation')),
    Field('marital_status', 'string', label=T('Marital Status')),
    Field('father_name', 'string', label=T('Father Name')),
    Field('mother_name', 'string', label=T('Mother Name')),
    Field('active_user', 'boolean', label=T('Active User')),
    )

db.define_table('register_codes',
    Field('citizen_id', db.citizen),
    Field('verification_code', 'string', unique=True),
    Field('code_date', 'date'),
    Field('used', 'boolean', default=False),
    )


db.define_table('police_reports',
    Field('citizen_id', db.citizen),
    Field('auth_user_id', db.auth_user),
    Field('incident_date', 'datetime', label=T('Incident Date')),
    Field('incident_description', 'text', label=T('Incident Description')),
    Field('picture', 'upload', label=T('Picture')),
    Field('crime_type', 'string', label=T('Crime Type')),
    Field('lat', 'double'),
    Field('lng', 'double'),
    Field('address', 'string', label=T('Address')),
    Field('perpetrator', 'string', label=T('Perpetrator')),
    Field('ip_address', 'string', default=request.client, label=T('IP Address')),
    Field('created_at', 'datetime', default=request.now)
    )

db.define_table('anonymous_report',
    Field('incident_date', 'datetime', label=T('Incident Date')),
    Field('incident_description', 'text', label=T('Incident Description')),
    Field('picture', 'upload', label=T('Picture')),
    Field('lat', 'double'),
    Field('lng', 'double'),
    Field('address', 'string', label=T('Address')),
    Field('perpetrator', 'string', label=T('Perpetrator')),
    Field('ip_address', 'string', default=request.client, label=T('IP Address')),
    Field('created_at', 'datetime', default=request.now),
    Field('icon', 'string'),
    Field('anonymous_id', 'integer'),
    Field('report_type', 'string') #type can be anything, like drugs, police corruption, etc
    )


db.define_table('report_codes',
    Field('police_reports_id', db.police_reports),
    Field('code', 'string', unique=True),
    Field('code_date', 'date'),
    )


db.define_table('wanted',
    Field('name', 'string', label=T('Name')),
    Field('last_name', 'string', label=T('Last Name')),
    Field('last_time_seen', 'date', label=T('Last Time Seen')),
    Field('picture', 'upload', label=T('Picture')),
    Field('crime', 'string', label=T('Crime')),
    Field('captured', 'boolean', default=False, label=T('Captured')),
    Field('age', 'integer', label=T('Age'))
    )

db.define_table('missing',
    Field('name', 'string', label=T('Name')),
    Field('last_name', 'string', label=T('Last Name')),
    Field('last_time_seen', 'date', label=T('Last Time Seen')),
    Field('picture', 'upload', label=T('Picture')),
    Field('missing_found', 'boolean', default=False, label=T('Captured')),
    Field('age', 'integer', label=T('Age'))
    )

db.define_table('wanted_data',
    Field('wanted_data_id', db.wanted),
    Field('description', 'string'),
    Field('ip_address', 'string', label=T('IP Address')),
    Field('created_at', 'datetime')
    )

db.define_table('missing_data',
    Field('missing_data_id', db.missing),
    Field('description', 'string'),
    Field('ip_address', 'string', label=T('IP Address')),
    Field('created_at', 'datetime')
    )


db.define_table('jurisdiction',
    Field('description', 'string'),
    )


db.define_table('police_station',
    Field('jurisdiction_id', db.jurisdiction),
    Field('name', 'string'),
    Field('lat', 'double'),
    Field('lng', 'double'),
    )

db.define_table('report_template',
    Field('text_template', 'text'),
    )

db.define_table('system_version',
    Field('version_number', 'integer'),
    )

import os
db.wanted.picture.uploadfolder = os.path.join(request.folder, "static/wanted/")
db.missing.picture.uploadfolder = os.path.join(request.folder, "static/missing/")


#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)
