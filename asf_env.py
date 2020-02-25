import os
import logging

def get_config():
    if 'MATURITY' not in os.environ.keys():
        logging.warning('os.environ[\'MATURITY\'] not set! Defaulting to prod config.]')
    return {
        'devel': {
            'bulk_download_api': 'https://bulk-download.asf.alaska.edu',
            'analytics_id': 'UA-118881300-4',
            'cmr_base': 'https://cmr.uat.earthdata.nasa.gov',
            'cmr_health': '/search/health',
            'cmr_api': '/search/granules.umm_json_v1_4',
            'cmr_collections': '/search/collections',
            'cmr_headers': {
                'Client-Id': 'vertex_asf'
            }
        },
        'test': {
            'bulk_download_api': 'https://bulk-download.asf.alaska.edu',
            'analytics_id': 'UA-118881300-3',
            'cmr_base': 'https://cmr.uat.earthdata.nasa.gov',
            'cmr_health': '/search/health',
            'cmr_api': '/search/granules.umm_json_v1_4',
            'cmr_collections': '/search/collections',
            'cmr_headers': {
                'Client-Id': 'vertex_asf'
            }
        },
        'prod': {
            'bulk_download_api': 'https://bulk-download.asf.alaska.edu',
            'analytics_id': 'UA-118881300-2',
            'cmr_base': 'https://cmr.earthdata.nasa.gov',
            'cmr_health': '/search/health',
            'cmr_api': '/search/granules.umm_json_v1_4',
            'cmr_collections': '/search/collections',
            'cmr_headers': {
                'Client-Id': 'vertex_asf'
            }
        },
        'prod-private': {
            'bulk_download_api': 'https://bulk-download.asf.alaska.edu',
            'analytics_id': 'UA-118881300-5',
            'cmr_base': 'https://cmr.earthdata.nasa.gov',
            'cmr_health': '/search/health',
            'cmr_api': '/search/granules.umm_json_v1_4',
            'cmr_collections': '/search/collections',
            'cmr_headers': {
                'Client-Id': 'vertex_asf'
            }
        }
    }[os.environ['MATURITY'] if 'MATURITY' in os.environ.keys() else 'prod']
