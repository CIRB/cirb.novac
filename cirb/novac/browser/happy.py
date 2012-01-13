# -*- coding: UTF-8 -*-
from zope.interface import implements, Interface

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from zope.component import getUtility
from plone.registry.interfaces import IRegistry

import logging, os, urllib, urllib2, socket, json
from urllib2 import URLError, HTTPError
from cirb.novac.browser.publicview import PUB_DOSSIER

class Happy(BrowserView):
    """
    happy pag browser view
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.logger = logging.getLogger('cirb.novac.happy')
        registry = getUtility(IRegistry)
        novac_url = os.environ.get("novac_url", None)
        if novac_url:
            self.novac_url = novac_url
        else:
            self.novac_url = registry['cirb.novac.novac_url']
        
        urbis_url = os.environ.get("urbis_url", None)
        if urbis_url:
            self.urbis_url = urbis_url
        else:
            self.urbis_url = registry['cirb.urbis.urbis_url']
            
        urbis_cache_url = os.environ.get("urbis_cache_url", None)
        if urbis_cache_url:
            self.urbis_cache_url = urbis_cache_url
        else:
            self.urbis_cache_url = registry['cirb.urbis.urbis_cache_url']
        
        rest_service = os.environ.get("rest_service", None)
        if rest_service:
            self.rest_service = rest_service
        else:
            self.rest_service = registry['cirb.novac.rest_service']        
    
    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()
    
    def happy(self):
        results={}
        results['sso'] = self.get_sso()
        results['waws'] = self.get_waws()
        results['urbis'] = self.get_urbis()
        results['access_database'] = self.access_database()
        results['plone_version'] = self.plone_version()
        return results
    
    def get_sso(self):
        return "sso"
    
    def get_waws(self):
        url = '%s/%s/100000' % (self.novac_url, PUB_DOSSIER)
        return get_service(url)
    
    def get_urbis(self):        
        url = "%s/gis/geoserver/nova/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=CLUSTER3KM&outputFormat=json" % self.context.portal_url()
        res_json = get_service(url)
        if res_json.get('status', '') == 'ko':
            return resutls
        resutls = json_proccessing(res_json.get("message"))
        tot = 0
        for feature in resutls.get('features'):
	    tot += feature.get('properties').get('NBR_DOSSIERS')
	return tot
            
    
    def access_database(self):
        return "db"
    
    def plone_version(self):
        return "plone_version"


def get_service(url, headers="", params=""):
    logger = logging.getLogger('cirb.novac.happy')
    oldtimeout = socket.getdefaulttimeout()
    results = ''
    if params:
        url = '%s?%s' % (url, params)
    try:
        socket.setdefaulttimeout(7) # let's wait 7 sec        
        request = urllib2.Request(url)
        for header in headers:
            try:
                request.add_header(header.keys()[0], header.values()[0])
            except:
                logger.info('headers bad formated')
        opener = urllib2.build_opener()
        results = opener.open(request).read()
    except HTTPError, e:
        exception = 'The server couldn\'t fulfill the request. URL : %s ' % url
        logger.error(exception)
        return {"status":'ko', "code":e.code, "message": e.msg}
    except URLError, e:
        exception =  'We failed to reach a server. URL: %s' % url
        logger.error(exception)
        return {"status":'ko', "code":e.code, "message": e.reason}
    finally:
        socket.setdefaulttimeout(oldtimeout)
    return {'status':'ok', "code":'200', 'message': results}
    
def json_proccessing(res_json):
    logger = logging.getLogger('cirb.novac.happy')
    print res_json
    try:
        jsondata = json.loads(res_json)
    except ValueError, e:
        msg_error = 'Json value error : %s.' % e.message
        logger.error(msg_error)
        return {"status":'ko', "message": msg_error}
    except SyntaxError, e:
        msg_error = 'Json bad formatted : %s.' % e.message
        logger.error(msg_error)
        return {"status":'ko', "message": msg_error}
    return jsondata
