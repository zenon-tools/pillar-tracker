import json
import datetime
from utils.http_wrapper import HttpWrapper


class NodeRpcWrapper(object):

    def __init__(self, node_url):
        self.node_url = node_url

    def get_latest_momentum(self):
        r = self.__ledger_get_frontier_momentum()
        if r.status_code == 200:
            d = json.loads(r.text)
            try:
                return {'height': d['result']['height'], 'timestamp': str(datetime.datetime.now())}
            except KeyError:
                return {'error': 'KeyError: get_latest_momentum'}
        else:
            return {'error': f'Bad response: get_latest_momentum {r.status_code}'}

    def get_all_pillars(self):
        r = self.__embedded_pillar_get_all()
        if r.status_code == 200:
            d = json.loads(r.text)
            pillars = {'pillars': {}, 'timestamp': str(
                datetime.datetime.now())}
            try:
                for pillar in d['result']['list']:
                    pillars['pillars'][pillar['ownerAddress']] = {'name': pillar['name'], 'ownerAddress': pillar['ownerAddress'], 'currentStats': pillar['currentStats'], 'weight': int(pillar['weight']),
                                                                  'giveMomentumRewardPercentage': pillar['giveMomentumRewardPercentage'], 'giveDelegateRewardPercentage': pillar['giveDelegateRewardPercentage'], 'rank': pillar['rank']}
            except KeyError:
                return {'error': 'KeyError: get_all_pillars'}
            return pillars
        else:
            return {'error': f'Bad response: get_all_pillars {r.status_code}'}

    def get_reward_epoch(self, address):
        r = self.__embedded_pillar_get_frontier_reward_by_page(address)
        if r.status_code == 200:
            d = json.loads(r.text)
            if len(d['result']['list']) > 0:
                try:
                    return {'epoch': d['result']['list'][0]['epoch'], 'reward': int(d['result']['list'][0]['znnAmount']), 'timestamp': str(datetime.datetime.now())}
                except KeyError:
                    return {'error': 'KeyError: get_reward_epoch'}
            else:
                return {'error': f'Result list empty: get_reward_epoch'}
        else:
            return {'error': f'Bad response: get_reward_epoch {r.status_code}'}

    def __ledger_get_frontier_momentum(self):
        return HttpWrapper.post(self.node_url, {'jsonrpc': '2.0', 'id': 1,
                                                'method': 'ledger.getFrontierMomentum', 'params': []})

    def __embedded_pillar_get_all(self, params=[0, 1000]):
        return HttpWrapper.post(self.node_url, {'jsonrpc': '2.0', 'id': 1,
                                                'method': 'embedded.pillar.getAll', 'params': params})

    def __embedded_pillar_get_frontier_reward_by_page(self, address):
        return HttpWrapper.post(self.node_url, {'jsonrpc': '2.0', 'id': 1,
                                                'method': 'embedded.pillar.getFrontierRewardByPage', 'params': [address, 0, 1]})
