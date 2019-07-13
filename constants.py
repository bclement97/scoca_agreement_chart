DEFAULT_START_DATE = '2019-01-03'  # This is the start of the newest Assoc. Justice's tenure (J. Groban).
DATE_FORMAT = '%Y-%m-%d'

DOCKET_LIST_ENDPOINT = 'https://www.courtlistener.com/api/rest/v3/dockets/'
DOCKET_LIST_FILTERS = {
    'court': 'cal',
    'clusters__date_filed__gte': DEFAULT_START_DATE,
    'order_by': ['-date_modified', '-date_created'],
}
OPINION_CLUSTER_ENDPOINT = 'https://www.courtlistener.com/api/rest/v3/clusters/{}/'  # {} is ID
OPINION_CLUSTER_FILTERS = {
    'fields': ['id', 'absolute_url', 'sub_opinions', 'date_filed', 'date_filed_is_approximate'],
}
OPINION_INSTANCE_ENDPOINT = 'https://www.courtlistener.com/api/rest/v3/opinions/{}/'  # {} is ID
OPINION_INSTANCE_FILTERS = {
    'fields': ['id', 'plain_text'],
}
