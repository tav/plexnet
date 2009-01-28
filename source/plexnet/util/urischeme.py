"""
===========
URI Schemes
===========

A list of known URI schemes compiled from various indexes.

    >>> 'http' in schemes
    True

    >>> 'mailto' in schemes
    True

    >>> 'plex' in schemes
    True

    >>> 'made-up-scheme-23' in schemes # hope this doesn't get registered ;p
    False

    >>> get_info('plex')
    'Plexnet'

    >>> get_info('plex', 'uri')
    'plex:ocsi/plexnet/urischeme'

    >>> # get_info('plex', 'full')

``schemes`` is a mapping with URI addressing schemes as keys and descriptions as
values. It was compiled from the index at
http://www.iana.org/assignments/uri-schemes.html and an older list at
http://www.w3.org/Addressing/schemes.html.

"""

from .pytype import SequenceType

__all__ = ['schemes', 'get_info']

# ------------------------------------------------------------------------------
# known uri schemes -- @/@ some should be filled in with useful deskriptions
# ------------------------------------------------------------------------------

schemes = {

    'about': 'Provides information on Navigator.',

    'acap': 'Application Configuration Access Protocol.',

    'addbook': "To add vCard entries to Communicator's Address Book",

    'afp': 'Apple Filing Protocol',

    'afs': 'Andrew File System global file names',

    'aim': 'AOL Instant Messenger',

    'callto': 'NetMeeting links',

    'castanet': 'Castanet Tuner URLs for Netcaster',

    'chttp': 'Cached HTTP supported by RealPlayer',

    'cid': 'Content Identifier',

    'data': ('Allows inclusion of small data items as "immediate" data.',
             'urn:rfc:2397'),

    'dav': ('Distributed Authoring and Versioning Protocol',
            'urn:rfc:2518'),

    'dns': 'Domain Name System resources',

    'eid': ('External ID; non-URL data; general escape mechanism to allow '
            'access to information for applications that are too '
            'specialized to justify their own schemes'),
    'fax': ('a connection to a terminal that can handle telefaxes '
            '(facsimiles); RFC 2806'),

    'feed' : 'NetNewsWire feed',

    'file': 'Host-specific file names',

    'finger': '',

    'freenet': 'Freenet',

    'ftp': 'File Transfer Protocol',

    'go': ('Go', 'urn:rfc:3368'),

    'gopher': 'The Gopher Protocol',

    'gsm-sms': 'Global System for Mobile Communications Short Message Service',

    'h323': 'Video (audiovisual) communication on local area networks',

    'h324': ('Video and audio communications over low bitrate connections '
             'such as POTS modem connections'),

    'hdl': 'CNRI handle system',

    'hnews': 'An HTTP-tunneling variant of the NNTP news protocol',

    'http': 'Hypertext Transfer Protocol',

    'https': 'HTTP over SSL',

    'hydra': ('SubEthaEdit URI.', 'http://www.codingmonkeys.de/subethaedit'),

    'iioploc': 'Internet Inter-ORB Protocol Location?',

    'ilu': 'Inter-Language Unification',

    'im': 'Instant Messaging',

    'imap': 'Internet Message Access Protocol',

    'ior': 'CORBA interoperable object reference',

    'ipp': 'Internet Printing Protocol',

    'irc': 'Internet Relay Chat',

    'iseek' : ('An OS X utility.', 'www.ambrosiasw.com'),

    'jar': 'Java archive',

    'javascript': 'JavaScript code; evaluates the expression after the colon',

    'jdbc': 'JDBC connection URI.',

    'ldap': 'Lightweight Directory Access Protocol',

    'lifn': '',

    'livescript': '',

    'lrq': '',

    'mailbox': 'Mail folder access',

    'mailserver': 'Access to data available from mail servers',

    'mailto': 'Electronic mail address',

    'md5': 'MD5 message-digest algorithm',

    'mid': 'Message identifier',

    'mnet': 'Mnet',

    'mocha': '',

    'modem': ('A connection to a terminal that can handle incoming data calls',
              'urn:rfc:2806'),

    'mupdate': 'Mailbox Update (MUPDATE) Protocol',

    'news': 'USENET news',

    'nfs': 'Network File System protocol',

    'nntp': 'USENET news using NNTP access',

    'opaquelocktoken': '',

    'phone': '',

    'plex': ('Plexnet', 'plex:ocsi/plexnet/urischeme'),

    'pop': 'Post Office Protocol',

    'pop3': 'Post Office Protocol v3',

    'pres': 'Presence',

    'printer': '',

    'prospero': 'Prospero Directory Service',

    'rdar' : ('URLs found in Darwin source',
              'http://www.opensource.apple.com/darwinsource/'),

    'res': '',

    'rtsp': 'Real Time Streaming Protocol',

    'rvp': '',

    'rwhois': '',

    'rx': 'Remote Execution',

    'sdp': '',

    'service': 'Service location',

    'shttp': 'Secure hypertext transfer protocol',

    'sip': 'Session Initiation Protocol',

    'sips': 'Secure session intitiaion protocol',

    'smb': 'SAMBA filesystems.',

    'snews': 'For NNTP postings via SSL',

    'soap.beep': '',

    'soap.beeps': '',

    'ssh': 'Reference to interactive sessions via ssh.',

    't120': 'Real time data conferencing (audiographics)',

    'tcp': '',

    'tel': (('A connection to a terminal that handles normal voice telephone '
             'calls, a voice mailbox or another voice messaging system or a '
             'service that can be operated using DTMF tones.'), 'urn:rfc:2806'),

    'telephone': 'Telephone',

    'telnet': 'Reference to interactive sessions',

    'tftp': 'Trivial File Transfer Protocol',

    'tip': 'Transaction Internet Protocol',

    'tn3270': 'Interactive 3270 emulation sessions',

    'tv': '',

    'urn': 'Uniform Resource Name',

    'uuid': 'Universally Unique Identifiers',

    'vemmi': 'Versatile multimedia interface',

    'videotex': '',

    'view-source': 'Displays HTML code that was generated with JavaScript',

    'wais': 'Wide Area Information Servers',

    'whodp': '',

    'whois++': 'Distributed directory service.',

    'x-man-page': ('Opens man pages in Terminal.app on OS X.',
                   'http://www.macosxhints.com'),

    'xmlrpc.beep': '',

    'xmlrpc.beeps': '',

    'z39.50r': 'Z39.50 Retrieval',

    'z39.50s': 'Z39.50 Session',

    }

level_mapper = {

    'description':0,
    'uri':1,
    'full':2

    }

def get_info(name, detail='description'):

    detail = level_mapper[detail]

    if name not in schemes:
        raise AttributeError

    info = schemes[name]

    if isinstance(info, SequenceType):
        return info[detail]

    return info
