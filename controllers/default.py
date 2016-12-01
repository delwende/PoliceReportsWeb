# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

@auth.requires_login()
def index():
    form = SQLFORM.grid(db.citizen,
        csv=auth.has_membership("admin"),
        create=auth.has_membership("admin"),
        details=False,
        editable=auth.has_membership("admin"),
        deletable=auth.has_membership("admin"),
        field_id=False,
        fields=[db.citizen.name,
            db.citizen.last_name,
            db.citizen.ssn,
            db.citizen.address,
            db.citizen.phone],
        links=[dict(header=T("Action"), body=lambda row: A(T("View"),
                _href=URL("default", "view_citizen_profile",
                args=[row.id])))],
               )
    return dict(form=form)


@auth.requires_login()
def view_citizen_profile():
    db.citizen.id.readable=False
    db.citizen.active_user.readable=False
    form = SQLFORM(db.citizen,
            request.args(0),
            deletable=False,
            readonly=True)
    return dict(form=form)


@auth.requires_login()
def add_wanted():
    db.wanted.id.readable=False
    db.wanted.picture.readable=False
    links = [dict(header = T("Picture"),body = lambda row: A(IMG(_src =
                    URL('default', 'download', args = row.picture),
                    _width = 100, _height = 100, _class="img-rounded"),
                _href = URL('default', 'download', args = row.picture))
    )]
    form = SQLFORM.smartgrid(db.wanted,
        csv=auth.has_membership("admin"),
        field_id=False,
        links=links)
    return dict(form=form)

@auth.requires_login()
def add_missing():
    db.missing.picture.readable=False
    links = [dict(header = T("Picture"),body = lambda row: A(IMG(_src =
                    URL('default', 'download', args = row.picture),
                    _width = 100, _height = 100, _class="img-rounded"),
                _href = URL('default', 'download', args = row.picture))
    )]
    db.missing.id.readable=False
    form = SQLFORM.smartgrid(db.missing,
        csv=auth.has_membership("admin"),
        field_id=False,
        links=links)
    return dict(form=form)


@auth.requires_login()
def police_reports():
    query = (db.police_reports.citizen_id==db.citizen.id)
    form = SQLFORM.grid(query,
            create=auth.has_membership("admin"),
            editable=auth.has_membership("admin"),
            deletable=auth.has_membership("admin"),
            details=auth.has_membership("admin"),
            csv=auth.has_membership("admin"),
            field_id=False,
            fields=[db.citizen.name,
                db.citizen.last_name,
                db.citizen.phone,
                db.police_reports.incident_date],
            links=[dict(header=T("Action"), body=lambda row: A(T("View"),
                _href=URL("default", "edit_police_report",
                args=[row.police_reports.id])))])
    return dict(form=form)


@auth.requires_login()
def corruption_reports():
    db.anonymous_report.id.readable=False
    db.anonymous_report.picture.readable=False
    db.anonymous_report.lat.readable=False
    db.anonymous_report.lng.readable=False
    links = [dict(header = T("Picture"),body = lambda row: A(IMG(_src =
                    URL('default', 'download', args = row.picture),
                    _width = 100, _height = 100, _class="img-rounded"),
                _href = URL('default', 'download', args = row.picture))
    )]
    query = db(db.anonymous_report.report_type == 'corruption')
    if query:
            form = SQLFORM.grid(query,
                    create=auth.has_membership("admin"),
                    editable=auth.has_membership("admin"),
                    deletable=auth.has_membership("admin"),
                    csv=auth.has_membership("admin"),
                    field_id=False,
                    fields=[
                        db.anonymous_report.perpetrator,
                        db.anonymous_report.picture,
                        db.anonymous_report.incident_description,
                        db.anonymous_report.incident_date],
                    links=links)
    else:
        form = CENTER(H2(T('No records to show')))
    return dict(form=form)


@auth.requires_login()
def edit_police_report():
    db.police_reports.id.readable=False
    db.police_reports.id.writable=False
    db.police_reports.picture.writable=False
    db.police_reports.incident_date.writable=False
    db.police_reports.incident_description.writable=False
    db.police_reports.citizen_id.readable=False
    db.police_reports.citizen_id.writable=False
    db.police_reports.lat.writable=False
    db.police_reports.lat.readable=False
    db.police_reports.lng.writable=False
    db.police_reports.lng.readable=False
    db.police_reports.address.writable=False
    db.police_reports.perpetrator.writable=False
    form = SQLFORM(db.police_reports,
            request.args(0),
            deletable=False,
            upload=URL(r=request,f='download')).process()
    #We assing the report to current officer
    select = form.element(_id="police_reports_auth_user_id__row")
    select["_style"] = "visibility: hidden;"
    option = form.element("option")
    option["_value"] = auth.user_id
    if form.accepted:
        redirect(URL('generate_report',
            args=request.args(0)))
    return dict(form=form)


@auth.requires_login()
def drugs_reports():
    return dict()


@auth.requires_login()
def suspect_aircraft():
    return dict()


@auth.requires_login()
def generate_report():
    report = db(db.police_reports.id==request.args(0)).select().first()
    citizen_id = report['citizen_id']
    citizen = db(db.citizen.id == citizen_id).select().first()
    officer = db(db.auth_user.id == auth.user_id).select().first()
    return dict(report=report, citizen=citizen, officer=officer)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()
