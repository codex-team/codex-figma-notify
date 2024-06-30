import json
import re
from api import FigmaAPI
from jycm.jycm import YouchamaJsonDiffer

class FigmaEventParser:

    NodeIDRegex = r'(\d+[:-]\d+)'

    def __init__(self, event, figma_api) -> None:
        self.event = event
        self.api = figma_api
        self.message_lines = []

    @staticmethod
    def convert_node_id(node_id):
        return node_id.replace(':', '-')
    
    @staticmethod
    def get_node_url_from_component(component):
        meta = component['meta']
        return f"{FigmaAPI.FIGMA_WEB}/{meta['file_key']}?node-id={FigmaEventParser.convert_node_id(meta['node_id'])}"

    def modified_components(self):
        modified_info = {
            'component_ids': set(),
            'components': []
        }
        component_ids = set()
        if 'modified_components' in self.event:
            for component in self.event['modified_components']:
                key = component['key']
                info = self.api.get_component_info(key)
                meta = info['meta']
                node_id = FigmaEventParser.convert_node_id(meta['node_id'])
                component_ids.add(node_id)

                if 'name' in meta['containing_frame']:
                    name = f"{meta['containing_frame']['name']}, {meta['name']}"
                else:
                    name = meta['name']

                modified_info['components'].append([node_id, name])
            
        modified_info['component_ids'] = component_ids
        return modified_info
    
    def created_components(self):
        created_info = {
            'component_ids': set(),
            'components': []
        }
        component_ids = set()
        if 'created_components' in self.event:
            for component in self.event['created_components']:
                key = component['key']
                info = self.api.get_component_info(key)
                meta = info['meta']
                component_ids.add(FigmaEventParser.convert_node_id(meta['node_id']))

                if 'name' in meta['containing_frame']:
                    name = f"{meta['containing_frame']['name']}, {meta['name']}"
                else:
                    name = meta['name']

                created_info['components'].append([meta['node_id'], name])
            
        created_info['component_ids'] = component_ids
        return created_info
    
    @staticmethod
    def traverse_path(obj, path):
        new_path = []
        cur = obj
        for key in path.split("->"):
            if key == "":
                return ""
            elif key[0]=='[' and key[-1]==']':
                cur = cur[int(key[1:-1])]
                if 'name' in cur:
                    new_path.append(f"({cur['name']})")
                elif isinstance(cur, str):
                    new_path.append(cur)
                else:
                    new_path.append(f"ERROR")
            else:
                cur=cur[key]
                new_path.append(key)
        return ' -> '.join(new_path)
    
    @staticmethod
    def flatten_object(obj, path):
        if  isinstance(obj, str):
            return obj
        else:
            if 'componentSetId' in obj:
                node_id = obj['componentSetId']
            elif 'id' in obj:
                node_id = obj['id']
            else:
                node_id = re.findall(FigmaEventParser.NodeIDRegex, path)[-1]
            return [FigmaEventParser.convert_node_id(node_id), obj['name']]
        
    def generate_history_diff(self, left, right):
        ycm = YouchamaJsonDiffer(left, right)
        ycm.diff()
        diff_result = ycm.to_dict(no_pairs=True)
        with open("diff.json", "w") as w:
            w.write(json.dumps(diff_result))

        if 'value_changes' in diff_result:
            for i, change in enumerate(diff_result['value_changes']):
                diff_result['value_changes'][i]['path'] = FigmaEventParser.traverse_path(left, change['left_path'])
                del diff_result['value_changes'][i]['left']
                del diff_result['value_changes'][i]['right']
                del diff_result['value_changes'][i]['left_path']
                del diff_result['value_changes'][i]['right_path']
        else:
            diff_result['value_changes'] = []

        if 'dict:add' in diff_result:
            for i, change in enumerate(diff_result['dict:add']):
                diff_result['dict:add'][i]['path'] = FigmaEventParser.traverse_path(right, change['right_path'])
                diff_result['dict:add'][i]['value'] = FigmaEventParser.flatten_object(change['right'], change['right_path'])
                del diff_result['dict:add'][i]['left']
                del diff_result['dict:add'][i]['right']
                del diff_result['dict:add'][i]['left_path']
                del diff_result['dict:add'][i]['right_path']
        else:
            diff_result['dict:add'] = []

        if 'list:add' in diff_result:
            for i, change in enumerate(diff_result['list:add']):
                diff_result['list:add'][i]['path'] = FigmaEventParser.traverse_path(right, change['right_path'])
                diff_result['list:add'][i]['value'] = FigmaEventParser.flatten_object(change['right'], change['right_path'])
                del diff_result['list:add'][i]['left']
                del diff_result['list:add'][i]['right']
                del diff_result['list:add'][i]['left_path']
                del diff_result['list:add'][i]['right_path']
        else:
            diff_result['list:add'] = []

        return diff_result