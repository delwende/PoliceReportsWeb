import gluon.contrib.simplejson as json

def call():
    session.forget()
    return service()

def random_color():
    import random
    color = "#%06x" % random.randint(0, 0xFFFFFF)
    return color


def random_id():
    import random
    id = random.randint(1, 2.14748e+09)
    return id


@service.json
def wanted():
	r=db(db.wanted).select()
	return dict(r=r)


@service.json
def wanted_data():
	insert = db.wanted_data.insert(description=request.vars.description,
		wanted_data_id=request.vars.wanted_data_id)
	return dict(status="ok")


@service.json
def missing():
	r=db(db.missing).select()
	return dict(r=r)


@service.json
def missing_data():
	data = json.loads(request.body.read())
	insert = db.missing_data.insert(description=data['description'],
		missing_data_id=data['missing_data_id'])
	return dict(status="ok")


def id_generator():
    import string
    import random
    size = 6
    chars = string.ascii_uppercase + string.digits
    verification_code = ''.join(random.choice(chars) for _ in range(size))
    return verification_code


@service.json
def register_citizen():
    data = json.loads(request.body.read())
    ssn = db(db.citizen.ssn == data['ssn']).select().first()
    email = db(db.citizen.email == data['email']).select().first()
    if ssn or email:
        return dict(status="already_registered")
    else:
        citizen = db.citizen.insert(
                                    ssn=data['ssn'],
                                    name=data['name'],
                                    last_name=data['last_name'],
                                    nationality=data['nationality'],
                                    birth_date=data['birth_date'],
                                    address=data['address'],
                                    phone=data['phone'],
                                    email=data['email'],
                                    occupation=data['occupation'],
                                    marital_status=data['marital_status'],
                                    mother_name=data['mother_name'],
                                    father_name=data['father_name']
                                    )
        verification_code = id_generator()
        db.register_codes.insert(
                                verification_code=verification_code,
                                citizen_id=citizen
                                )
        subject = 'Gracias por su registro'
        message = 'El código de verificación es: \n'
        message += str(verification_code)
        message += '\n Ingreselo en la aplicación para completar su registro'
        mail.send(to=data['email'], subject=subject, message=message)
        return dict(status="registered")


@service.json
def activation():
    data = json.loads(request.body.read())
    if data['ssn']:
        citizen_id = db(db.citizen.ssn == data['ssn']).select().first()
        code = db((db.register_codes.used == False)&
                (db.register_codes.citizen_id == citizen_id['id'])).select().last()
    if code:
        if data['verification_code'] == code['verification_code']:
            code.update_record(used=True, code_date=data['code_date'], citizen_id=citizen_id['id'])
            citizen_id.update_record(active_user=True, citizen_id=citizen_id['id'])
            return dict(status="activation_successful",
                    citizen_id=citizen_id['id'])
        else:
            return dict(status="activation_error")
    else:
        return dict(status="error")

@service.json
def login():
    data = json.loads(request.body.read())
    ssn = db(db.citizen.ssn == data['ssn']).select().first()
    if ssn:
        verification_code = id_generator()
        db.register_codes.insert(
                                verification_code=verification_code,
                                code_date=data['code_date'],
                                citizen_id=ssn['id']
                                )
        subject = 'Código de inicio de sesión'
        message = 'El código de inicio de sesión es: \n'
        message += str(verification_code)
        message += '\n Ingreselo en la aplicación para acceder al sistema'
        mail.send(to=ssn['email'], subject=subject, message=message)
        return dict(status="login_successful")
    else:
        return dict(status="error")


@service.json
def police_report():
    if hasattr(request.vars.picture, 'filename'):
        file = open('/tmp/'+str(request.vars.picture.filename), 'wb')
        image = request.vars.picture.file.read()
        file.write(image)
        file.close()
        file = open('/tmp/'+str(request.vars.picture.filename), 'rb')
        citizen_id = db(db.citizen.ssn == request.vars.ssn).select().first()
        if citizen_id:
            db.police_reports.insert(
                    citizen_id=citizen_id,
                    incident_date=request.vars.incident_date,
                    incident_description=request.vars.incident_description,
                    picture=db.police_reports.picture.store(file, request.vars.picture.filename),
                    lat=request.vars.lat,
                    lng=request.vars.lng,
                    address=request.vars.address,
                    perpetrator=request.vars.perpetrator
                    )
            file.close()
            return dict(status="ok")
        else:
            return dict(status="error")
    else:
        citizen_id = db(db.citizen.ssn == request.vars.ssn).select().first()
        if citizen_id:
            db.police_reports.insert(
                    citizen_id=citizen_id,
                    incident_date=request.vars.incident_date,
                    incident_description=request.vars.incident_description,
                    lat=request.vars.lat,
                    lng=request.vars.lng,
                    address=request.vars.address,
                    perpetrator=request.vars.perpetrator
                    )
            return dict(status="ok")
        else:
            return dict(status="error")


@service.json
def drugs_reports():
    markers = db(db.anonymous_report.report_type=='drugs').select()
    return markers.as_json()

@service.json
def suspect_aircraft():
    markers = db(db.anonymous_report.report_type=='suspect_aircraft').select()
    return markers.as_json()



@service.json
def police_stations():
    police_stations = db(db.jurisdiction.id == db.police_station.jurisdiction_id).select(db.police_station.name,
            db.police_station.lat,
            db.police_station.lng,
            db.police_station.id,
            db.police_station.jurisdiction_id)
    return dict(police_stations=police_stations)

@service.json
def anonymous_report():
    if request.vars.anonymous_id:
        import datetime
        last_report = db((db.anonymous_report.anonymous_id == request.vars.anonymous_id)
            &(db.anonymous_report.created_at >= datetime.datetime.today().strftime("%Y-%m-%d 00:00:00"))).select(db.anonymous_report.marker_color,
             db.anonymous_report.created_at)
        if len(last_report) > 2:
            if last_report[-1]['created_at'] <= datetime.datetime.now() - datetime.timedelta(minutes=30):
                last_report = db((db.anonymous_report.anonymous_id == request.vars.anonymous_id)).select(db.anonymous_report.marker_color, limitby=(0,1)).first()
                if hasattr(request.vars.picture, 'filename'):
                    file = open('/tmp/'+str(request.vars.picture.filename), 'wb')
                    image = request.vars.picture.file.read()
                    file.write(image)
                    file.close()
                    file = open('/tmp/'+str(request.vars.picture.filename), 'rb')
                    db.anonymous_report.insert(
                            incident_date=request.vars.incident_date,
                            incident_description=request.vars.incident_description,
                            picture=db.police_reports.picture.store(file, request.vars.picture.filename),
                            lat=request.vars.lat,
                            lng=request.vars.lng,
                            address=request.vars.address,
                            perpetrator=request.vars.perpetrator,
                            anonymous_id=request.vars.anonymous_id,
                            marker_color=last_report['marker_color'],
                            report_type=request.vars.report_type
                            )
                    file.close()
                    return dict(status="ok")
                else:
                    last_report = db((db.anonymous_report.anonymous_id == request.vars.anonymous_id)).select(db.anonymous_report.marker_color, limitby=(0,1)).first()
                    db.anonymous_report.insert(
                            incident_date=request.vars.incident_date,
                            incident_description=request.vars.incident_description,
                            lat=request.vars.lat,
                            lng=request.vars.lng,
                            address=request.vars.address,
                            perpetrator=request.vars.perpetrator,
                            anonymous_id=request.vars.anonymous_id,
                            marker_color=last_report['marker_color'],
                            report_type=request.vars.report_type
                            )
                    return dict(status="ok")
            else:
                return dict(status = "cool_down")
        else:
            last_report = db((db.anonymous_report.anonymous_id == request.vars.anonymous_id)).select(db.anonymous_report.marker_color, limitby=(0,1)).first()
            if hasattr(request.vars.picture, 'filename'):
                file = open('/tmp/'+str(request.vars.picture.filename), 'wb')
                image = request.vars.picture.file.read()
                file.write(image)
                file.close()
                file = open('/tmp/'+str(request.vars.picture.filename), 'rb')
                db.anonymous_report.insert(
                        incident_date=request.vars.incident_date,
                        incident_description=request.vars.incident_description,
                        picture=db.police_reports.picture.store(file, request.vars.picture.filename),
                        lat=request.vars.lat,
                        lng=request.vars.lng,
                        address=request.vars.address,
                        perpetrator=request.vars.perpetrator,
                        anonymous_id=request.vars.anonymous_id,
                        marker_color=last_report['marker_color'],
                        report_type=request.vars.report_type
                        )
                file.close()
                return dict(status="ok")
            else:
                last_report = db((db.anonymous_report.anonymous_id == request.vars.anonymous_id)).select(db.anonymous_report.marker_color, limitby=(0,1)).first()
                db.anonymous_report.insert(
                        incident_date=request.vars.incident_date,
                        incident_description=request.vars.incident_description,
                        lat=request.vars.lat,
                        lng=request.vars.lng,
                        address=request.vars.address,
                        perpetrator=request.vars.perpetrator,
                        anonymous_id=request.vars.anonymous_id,
                        marker_color=last_report['marker_color'],
                        report_type=request.vars.report_type
                        )
                return dict(status="ok")
    else:
        color = random_color()
        anonymous_id = random_id()
        if hasattr(request.vars.picture, 'filename'):
            file = open('/tmp/'+str(request.vars.picture.filename), 'wb')
            image = request.vars.picture.file.read()
            file.write(image)
            file.close()
            file = open('/tmp/'+str(request.vars.picture.filename), 'rb')
            db.anonymous_report.insert(
                    incident_date=request.vars.incident_date,
                    incident_description=request.vars.incident_description,
                    picture=db.police_reports.picture.store(file, request.vars.picture.filename),
                    lat=request.vars.lat,
                    lng=request.vars.lng,
                    address=request.vars.address,
                    perpetrator=request.vars.perpetrator,
                    anonymous_id=anonymous_id,
                    marker_color=color,
                    report_type=request.vars.report_type
                    )
            file.close()
            return dict(status="ok", anonymous_id=anonymous_id)
        else:
            db.anonymous_report.insert(
                    incident_date=request.vars.incident_date,
                    incident_description=request.vars.incident_description,
                    lat=request.vars.lat,
                    lng=request.vars.lng,
                    address=request.vars.address,
                    perpetrator=request.vars.perpetrator,
                    anonymous_id=anonymous_id,
                    marker_color=color,
                    report_type=request.vars.report_type
                    )
            return dict(status="ok", anonymous_id=anonymous_id)

@service.json
def sms_websocket():
    data = json.dumps(request.body.read())
    from gluon.contrib.websocket_messaging import websocket_send
    websocket_send('http://127.0.0.1:8888', data, 'mykey', 'sms_websocket')
