""" Obscure the session id when passing it around in HTML """
from django.conf import settings
from urlparse import urlparse
from cookieless.xteacrypt import crypt

class CryptSession(object):
    """ Tool to generate encrypted session id for 
        middleware or templatetags 
    """
    def __init__(self):
        self.secret = settings.SECRET_KEY[:16]

    def prepare_url(self, url):
        patt = None
        if url.find('?') == -1:
            patt = '%s?'
        else:
            patt = '%s&amp;'
        return patt % (url,)

    def encrypt(self, request, sessionid):
        """ Avoid showing plain sessionids """  
        if not sessionid:
            return ''
        secret = self._secret(request)
        return crypt(secret, sessionid).encode('hex')

    def decrypt(self, request, sessionid):
        """ Avoid showing plain sessionids 
            Optionally require that a referer exists and matches the 
            whitelist, or reset the session
        """
        if not sessionid:
            return ''
        secret = self._secret(request)
        if getattr(settings, 'COOKIELESS_HOSTS', []):
            referer = request.META.get('HTTP_REFERER', 'None')
            if referer == 'None':
                # End session unless a referer is passed
                return ''
            url = urlparse(referer)
            if url.hostname not in settings.COOKIELESS_HOSTS:
                err = '%s is unauthorised' % url.hostname
                raise Exception(err)
        return crypt(secret, sessionid.decode('hex'))

    def key_tuple(self, request):
        """ For use in generated html """
        return (settings.SESSION_COOKIE_NAME, 
                self.encrypt(request, request.session.session_key))

    def _secret(self, request):
        """ optionally make secret client dependent 
        """
        if getattr(settings, 'COOKIELESS_CLIENT_ID', False):
            ip = request.META['REMOTE_ADDR']
            agent = request.META['HTTP_USER_AGENT']
            secret = crypt(self.secret, agent + ip)[:16]
            return secret
        else:
            return self.secret