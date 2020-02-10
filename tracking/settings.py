from django.conf import settings

TRACK_AJAX_REQUESTS = getattr(settings, 'TRACK_AJAX_REQUESTS', False)
TRACK_ANONYMOUS_USERS = getattr(settings, 'TRACK_ANONYMOUS_USERS', True)
TRACK_SUPERUSERS = getattr(settings, 'TRACK_SUPERUSERS', True)

TRACK_PAGEVIEWS = getattr(settings, 'TRACK_PAGEVIEWS', False)

TRACK_IGNORE_URLS = getattr(settings, 'TRACK_IGNORE_URLS', (
    r'^(favicon\.ico|robots\.txt)$',
))

TRACK_IGNORE_USER_AGENTS = getattr(settings, 'TRACK_IGNORE_USER_AGENTS', tuple())

TRACK_IGNORE_STATUS_CODES = getattr(settings, 'TRACK_IGNORE_STATUS_CODES', [])

TRACK_USING_GEOIP = getattr(settings, 'TRACK_USING_GEOIP', False)
if hasattr(settings, 'TRACKING_USE_GEOIP'):
    raise DeprecationWarning('TRACKING_USE_GEOIP is now TRACK_USING_GEOIP')

TRACK_REFERER = getattr(settings, 'TRACK_REFERER', False)

TRACK_QUERY_STRING = getattr(settings, 'TRACK_QUERY_STRING', False)

TRACK_PAGING_SIZE = getattr(settings, 'TRACK_PAGING_SIZE', 100)

TRACK_REQ_BODY = getattr(settings, 'TRACK_REQ_BODY', False)

TRACK_REQ_BODY_CONTENT_TYPES = getattr(
    settings,
    'TRACK_REQ_BODY_CONTENT_TYPES',
    {
        'application/json',
        'multipart/form-data',
    }
)

TRACK_REQ_BODY_MAX_LEN = getattr(
    settings,
    'TRACK_REQ_BODY_MAX_BYTES',
    10240
)

TRACK_REQ_BODY_ACCEPTED_ENCODINGS = getattr(
    settings,
    'TRACK_REQ_BODY_ACCEPTED_ENCODINGS',
    'UTF-8',
)
