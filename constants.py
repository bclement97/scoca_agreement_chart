DEFAULT_START_DATE = '2019-01-03'  # This is the start of the newest Assoc. Justice's tenure (J. Groban).
DATE_FORMAT = '%Y-%m-%d'
COURTLISTENER_BASE_URL = 'https://www.courtlistener.com'
COURTLISTENER_REST_API = COURTLISTENER_BASE_URL + '/api/rest/v3'

DOCKET_LIST_ENDPOINT = COURTLISTENER_REST_API + '/dockets/'
DOCKET_LIST_FILTERS = {
    'court': 'cal',
    'clusters__date_filed__gte': DEFAULT_START_DATE,
    'order_by': ['-date_modified', '-date_created'],
}
OPINION_CLUSTER_ENDPOINT = COURTLISTENER_REST_API + '/clusters/{}/'  # {} is ID
OPINION_CLUSTER_FILTERS = {
    # As of 25-Jun-2019, the CourtListener API implementation always sets the following fields as such, but would be
    # useful for our purposes if the implementation changes in the future:
    # - panel, non_participating_judges, judges: empty/null
    'fields': ['id', 'absolute_url', 'panel', 'non_participating_judges', 'sub_opinions', 'judges', 'date_filed',
               'date_filed_is_approximate']
}
OPINION_INSTANCE_ENDPOINT = COURTLISTENER_REST_API + '/opinions/{}/'  # {} is ID
OPINION_INSTANCE_FILTERS = {
    # As of 25-Jun-2019, the CourtListener API implementation always sets the following fields as such, but would be
    # useful for our purposes if the implementation changes in the future:
    # - author, joined_by, author_str: empty/null
    # - type: '010combined'
    'fields': ['id', 'author', 'joined_by', 'author_str', 'type', 'sha1', 'download_url', 'plain_text'],
}

DEFAULT_REQUESTS_HEADER = {'Accept': 'application/json'}
