class PATH_NAMES(object):
    """ Path names for internal IBEIS database """
    sqldb  = '_ibeis_database.sqlite3'
    _ibsdb = '_ibsdb'
    cache  = '_ibeis_cache'
    chips  = 'chips'
    flann  = 'flann'
    images = 'images'
    qres   = 'qres'
    bigcache = 'bigcache'
    detectimg = 'detectimg'
    thumbs = 'thumbs'

# Names normalized to the standard UNKNOWN_NAME
ACCEPTED_UNKNOWN_NAMES = set(['Unassigned'])


# Name used to denote that idkwtfthisis
UNKNOWN_NAME = '____'
ENCTEXT_PREFIX = 'enc_'

# Pre-defined set of valid label keys/categories
LABEL_KEYS = {
"INDIVIDUAL_KEY": 0, 
"SPECIES_KEY": 1,
}
