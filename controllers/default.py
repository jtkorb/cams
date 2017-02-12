# -*- coding: utf-8 -*-

import requests
from datetime import datetime

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
    loads = DIV()
    for camera in db(db.cameras).select():
        loads.append(LOAD('default', 'single', ajax=True, args=[camera.id], vars={'refresh': "no"}, user_signature=True,
                          content=IMG(_src=URL('static', 'images/spinner.gif'), _style="width:100%;max-width:600px;box-shadow: 8px 8px 10px #aaa")))
    return dict(content=loads)


@auth.requires_signature()
def single():
    camera_id = request.args(0)

    image_row = db(db.images.camera_id == camera_id).select(orderby=db.images.time).last()
    message = "from cache"

    if request.vars.refresh == "yes" or image_row is None:
        image_row, message = fetch_image()
    return get_image(camera_id, image_row, message)


@auth.requires_signature()
def fetch_image():
    import time

    camera_id = request.args(0)
    camera = db(db.cameras.id == camera_id).select().first()

    usr = camera.usr
    pwd = camera.pwd
    fqdn = camera.fqdn
    name = camera.name
    port = camera.port
    camera_url = "http://%s:%s/cgi-bin/CGIProxy.fcgi?cmd=snapPicture2&usr=%s&pwd=%s" % (fqdn, port, usr, pwd)

    try:
        t1 = time.time()
        r = requests.get(camera_url, stream=True, timeout=15)
        t2 = time.time()
        id = db.images.insert(camera_id=camera_id, time=datetime.now(), image=db.images.image.store(r.raw, name + ".jpg"))
        image_row = db(db.images.id == id).select().first()
        message = "%.2f seconds" % (t2 - t1)
    except Exception as e:
        print("exception %s" % e)
        image_row = None
        message = "exception %s" % e

    return image_row, message


def get_image(camera_id, image_row, message):
    if image_row:
        caption = "Image received %s (%s); click to fetch new image." % (image_row.time, message)
        image_url = URL('download', args=image_row.image)
    else:
        target_id_err = camera_id + "_err"
        caption = DIV(DIV("Image not currently available (",
                          SPAN("click for detail", _onclick="jQuery('#%s').slideToggle()" % target_id_err),
                          "); click image area to try again."),
                      DIV(TT(message), _style="display: none;", _id=target_id_err))
        image_url = URL('static', 'images/missing.png')

    image = A(IMG(_src=image_url, _style="width:100%;max-width:600px;box-shadow: 8px 8px 10px #aaa"),
              _href=URL('default', 'single', args=[camera_id], vars={'refresh': 'yes'}, user_signature=True),
              _disable_with=IMG(_src=URL('static', 'images/spinner.gif'), _style="width:100%;max-width:600px;box-shadow: 8px 8px 10px #aaa").xml(),
              cid=request.cid)

    return DIV(DIV(image, _style="margin-bottom:5px"),
               DIV(caption, _style="margin-bottom:10px"))


# @auth.requires_login()
# def index():
#     """
#     Determine camera names and launch ajax to start the snap.
#     """
#     targets = DIV()
#     loaders = ""
#
#     cameras = db(db.cameras).select(db.cameras.id)
#     for camera in cameras:
#         id = camera.id
#         # if id > 2: continue  # uncomment to ignore Ellen's cameras
#         target_id = "target_%d" % id
#         targets.append(DIV(IMG(_src=URL('static', 'images/spinner.gif'), _style="width:100%;max-width:600px;"), _id=target_id,
#                            _style="display:inline-block;margin-right:20px;margin-bottom:50px;"))
#         loaders += "ajax('%s', ['name'], '%s');" % (URL('get_snap', args=[id], vars=request.vars), target_id)
#     script = SCRIPT("jQuery(document).ready(function(){" + loaders + "});")
#
#     return dict(content=DIV(targets, script))
#
#
# @auth.requires_login()
# def get_snap():
#     import time
#
#     camera_id = request.args(0)
#     camera = db(db.cameras.id == camera_id).select().first()
#
#     usr = camera.usr
#     pwd = camera.pwd
#     fqdn = camera.fqdn
#     name = camera.name
#     port = camera.port
#
#     image_id = None
#     print("request.vars.use_cache = %s" % request.vars.use_cache)
#     if (request.vars.use_cache is None) or (request.vars.use_cache == "yes"):
#         image_id = db(db.images.camera_id == camera_id).select(orderby=db.images.time).last()
#
#     print("1st image_id = %s" % image_id)
#
#     t1 = time.time()
#     if image_id is None:
#         camera_url = "http://%s:%s/cgi-bin/CGIProxy.fcgi?cmd=snapPicture2&usr=%s&pwd=%s" % (fqdn, port, usr, pwd)
#         print("sending request: %s" % camera_url)
#         try:
#             r = requests.get(camera_url, stream=True, timeout=5)
#         except Exception as e:
#             print("exception %s" % e)
#             r = None
#         print("r = %s" % r)
#         if r is None:
#             image_id = None
#         else:
#             image_id = db.images.insert(camera_id=camera_id, time=datetime.now(),
#                                         image=db.images.image.store(r.raw, name + ".jpg"))
#     t2 = time.time()
#
#     print("2nd image_id = %s" % image_id)
#
#     if image_id is None:
#         return DIV("time out")
#     else:
#         image = db(db.images.id == image_id).select().first().image
#
#         print("image = %s" % image)
#
#         anchor = A(IMG(_src=URL('download', args=image),
#                        _style="width:100%;max-width:600px;box-shadow: 8px 8px 10px #aaa"),
#                     _href=URL('fullsize', args=image))
#         return DIV(DIV(anchor, _style="margin-bottom:10px"), DIV("Time to snap: %.2f seconds" % (t2-t1)))


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

