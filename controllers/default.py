# -*- coding: utf-8 -*-

import requests

if False:
    from gluon import *
    from applications.eve.controllers.db import *
    from applications.eve.controllers.db import auth
    from applications.eve.controllers.db import myconf
    from applications.eve.controllers.db import service
    db = current.db
    response = current.response
    request = current.request
    cache = current.cache
    T = current.T


@auth.requires_login()
def index():
    """
    Determine camera names and launch ajax to start the snap.
    """
    names = myconf.get('app.names').split()

    targets = DIV()
    loaders = ""
    for name in names:
        target_id = "target_%s" % name
        targets.append(DIV(IMG(_src=URL('static', 'images/spinner.gif'), _style="width:100%;max-width:600px;"), _id=target_id,
                           _style="display:inline-block;margin-right:20px;margin-bottom:50px;"))
        loaders += "ajax('%s', ['name'], '%s');" % (URL('get_snap', args=[name]), target_id)
    script = SCRIPT("jQuery(document).ready(function(){" + loaders + "});")

    return dict(content=DIV(targets, script))


@auth.requires_login()
def get_snap():
    import time

    name = request.args[0]

    login = myconf.get('app.login')
    password = myconf.get('app.password')
    host = myconf.get('app.host')
    names = myconf.get('app.names').split()
    ports = myconf.get('app.ports').split()

    port = None
    for i in range(len(names)):
        if names[i] == name:
            port = ports[i]
            break
    assert port is not None

    camera_url = "http://%s:%s/cgi-bin/CGIProxy.fcgi?cmd=snapPicture2&usr=%s&pwd=%s" % (host, port, login, password)

    t1 = time.time()
    r = requests.get(camera_url, stream=True)
    image_id = db.images.insert(name=name, image=db.images.image.store(r.raw, name + ".jpg"))
    t2 = time.time()

    rows = db(db.images).select()
    row = rows.find(lambda row: row.id == image_id).first()

    anchor = A(IMG(_src=URL('download', args=row.image), _style="width:100%;max-width:600px;box-shadow: 8px 8px 10px #aaa"),
               _href=URL('fullsize', args=row.image))

    return DIV(DIV(anchor, _style="margin-bottom:10px"),
               DIV("Time to snap: %.2f seconds" % (t2-t1)))


@auth.requires_login()
def fullsize():
    return dict(content=IMG(_src=URL('download', args=request.args)))


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
