# -*- coding: utf-8 -*-

import requests

if False:
    from gluon import *
    from applications.eve.controllers.db import *
    from applications.eve.controllers.db import auth
    from applications.eve.controllers.db import myconf
    db = current.db
    response = current.response
    request = current.request
    cache = current.cache
    T = current.T

@auth.requires_login()
def index():
    """
    """
    login = myconf.get('app.login')
    password = myconf.get('app.password')
    host = myconf.get('app.host')

    names = myconf.get('app.names').split()
    ports = myconf.get('app.ports').split()

    row_list = []
    for i in range(len(ports)):
        port = ports[i]
        name = names[i]
        url = "http://%s:%s/cgi-bin/CGIProxy.fcgi?cmd=snapPicture2&usr=%s&pwd=%s" % (host, port, login, password)
        r = requests.get(url, stream=True)
        row_list.append(db.images.insert(name=name, image=db.images.image.store(r.raw, name + ".jpg")))

    content = DIV()
    rows = db(db.images).select()
    rows = rows.find(lambda row: row.id in row_list)
    for row in rows:
        content.append(A(IMG(_src=URL('download', args=row.image), _width=400), _href=URL('fullsize', args=row.image), _target="_blank"))
        content.append(" ")

    return dict(content=content)

def fullsize():
    return IMG(_src=URL('download', args=request.args))

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
    response.flash = None
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


