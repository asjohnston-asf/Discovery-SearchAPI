from flask import Response, make_response
import requests
import logging
from datetime import datetime
from CMR.Query import CMRQuery
from CMR.Translate import translate_params, input_fixer, output_translators
from CMR.Exceptions import CMRError
from Analytics import post_analytics
from asf_env import get_config

class APIProxyQuery:
    
    def __init__(self, request):
        self.request = request  # store the incoming request
        self.cmr_params = {}
        self.output = 'metalink'
        self.max_results = None
        
    def can_use_cmr(self):
        # make sure the provided params are a subset of the CMR-supported params and have compatible values
        try:
            self.cmr_params, self.output, self.max_results = translate_params(self.request.values)
            self.cmr_params = input_fixer(self.cmr_params)
        except ValueError as e: # didn't parse, pass it to the legacy API for now
            logging.debug('ValueError: {0}'.format(e))
            return False
        return True
    
    def get_response(self):
        # pick a backend and go!
        events = [{'ec': 'Param', 'ea': v} for v in self.request.values]
        events.append({'ec': 'Param List', 'ea': ', '.join(sorted([p.lower() for p in self.request.values]))})
        if self.can_use_cmr():
            logging.debug('get_response(): using CMR backend')
            events.append({'ec': 'Proxy Search', 'ea': 'CMR'})
            post_analytics(pageview=True, events=events)
            try:
                results = self.query_cmr()
                (translator, mimetype, suffix) = output_translators().get(self.output, output_translators()['metalink'])
                filename = 'asf-datapool-results-{0}.{1}'.format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), suffix)
                response = make_response(translator(results))
                response.headers.set('Content-Type', mimetype)
                response.headers.set('Content-Disposition', 'attachment', filename=filename)
                return response
            except CMRError as e:
                return make_response('A CMR error has occured: {0}'.format(e))
        else:
            logging.debug('get_response(): using ASF backend')
            events.append({'ec': 'Proxy Search', 'ea': 'Legacy'})
            post_analytics(pageview=True, events=events)
            return self.query_asf()
        
    # ASF API backend query
    def query_asf(self):
        # preserve GET/POST approach when querying ASF API
        logging.warning('Using Legacy as backend, from {0}'.format(self.request.access_route[-1]))
        if self.request.method == 'GET':
            param_string = 'api_proxy=1&{0}'.format(self.request.query_string.decode('utf-8'))
            r = requests.get('{0}?{1}'.format(get_config()['asf_api'], param_string))
        else: # self.request.method == 'POST':
            params = self.request.form
            params['api_proxy'] = 1
            param_string = '&'.join(['{0}={1}'.format(p, params[p]) for p in params])
            r = requests.post(get_config()['asf_api'], data=self.request.form)
        post_analytics(pageview=False, events=[{'ec': 'ASF API Status', 'ea': r.status_code}])
        if r.status_code != 200:
            logging.warning('Received status_code {0} from ASF API with params {1}'.format(r.status_code, param_string))
            return Response(r.text, r.status_code, r.headers.items())
        return make_response(r.text)
        
    # CMR backend query
    def query_cmr(self):
        logging.debug('Using CMR as backend, from {0}'.format(self.request.access_route[-1]))
        q = CMRQuery(params=self.cmr_params, output=self.output, max_results=self.max_results)
        r = q.get_results()
        
        return r
