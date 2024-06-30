import os
import requests
from dotenv import load_dotenv

class FigmaAPI:

    API_V1 = 'https://api.figma.com/v1'
    FIGMA_WEB = 'https://www.figma.com/design'

    def __init__(self, token, limit=5):
        self._token = token
        self.limit = limit
        self.headers = {
            'X-FIGMA-TOKEN': self._token,
        }
        self.timeout = 10

    @staticmethod
    def load_from_env():
        load_dotenv(override=True)
        token = os.getenv('API_TOKEN')
        limit = int(os.getenv('LIMIT', 10))
        return FigmaAPI(token=token, limit=limit)
    
    def get_node_url_from_component(self, component):
        meta = component['meta']
        return f"{FigmaAPI.FIGMA_WEB}/{meta['file_key']}?node-id={meta['node_id'].replace(':', '-')}"
        
    def get_component_info(self, key):
        r = requests.get(f"{FigmaAPI.API_V1}/components/{key}", headers=self.headers, timeout=self.timeout)
        if r.status_code != 200:
            print(f"Cannot get info of {key} component: {r.text}")
            return None
        else:
            return r.json()
        
    def get_versions(self, key):
        r = requests.get(f"{FigmaAPI.API_V1}/files/{key}/versions", headers=self.headers, timeout=self.timeout)
        if r.status_code != 200:
            print(f"Cannot get info of {key} versions: {r.text}")
            return None
        else:
            return list(map(lambda x: x['id'], filter(lambda x: x['label'] is not None, r.json()["versions"])))[:2]
        
    def get_history(self, key, ids, version):
        r = requests.get(f"{FigmaAPI.API_V1}/files/{key}?ids={','.join(ids)}&version={version}", headers=self.headers, timeout=self.timeout)
        if r.status_code != 200:
            print(f"Cannot get history of {key} for ids={ids} version: {version}")
            return None
        else:
            return r.json()

class Component:

    def __init__(self, data) -> None:
        self.data = data

    def __str__(self) -> str:
        pass