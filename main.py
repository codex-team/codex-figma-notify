import json
import requests
import re
from api import FigmaAPI
from event_parser import FigmaEventParser
from flask import Flask, request
import json
import os
from datetime import datetime
import random

app = Flask(__name__)
limit = 10
changes_limit = 10
figma_api = FigmaAPI.load_from_env()

def generate_report(event, created, modified):
    def insert_link_to_path(path):
        nodes = re.findall(r'(\d+[-:]\d+)', path)
        for node in nodes:
            if node in components_dict:
                path = path.replace(node, f"<a href='{FigmaAPI.FIGMA_WEB}/{file_key}?node-id={node}'>{components_dict[node]}</a>")
        return path
    lines = []
    file_key = event['file_key']

    components_dict = {}
    for obj in created:
        components_dict[obj[0]] = obj[1]
        components_dict[obj[0].replace('-', ':')] = obj[1]
    for obj in modified:
        components_dict[obj[0]] = obj[1]
        components_dict[obj[0].replace('-', ':')] = obj[1]

    lines.append(f"🛍 {event['triggered_by']['handle']} published <a href='{FigmaAPI.FIGMA_WEB}/{file_key}'>{event['file_name']}</a>")
    
    if event['description'] != "":
        lines.append(f"\n<blockquote>{event['description']}</blockquote>")

    if len(created):
        lines.append("\n<b>Created components</b>\n")
        for component in created[:limit]:
            lines.append(f"<a href='{FigmaAPI.FIGMA_WEB}/{file_key}?node-id={component[0]}'>{component[1]}</a>")
        if len(created) > limit:
            lines.append(f"<u>and {len(created)-limit} more</u>")

    if len(modified):
        lines.append("\n<b>Modified components</b>\n")
        for component in modified[:limit]:
            lines.append(f"<a href='{FigmaAPI.FIGMA_WEB}/{file_key}?node-id={component[0]}'>{component[1]}</a>")
        if len(modified) > limit:
            lines.append(f"<u>and {len(modified)-limit} more</u>")

    return "\n".join(lines)


@app.route('/', methods=['POST'])
def store_json():
    # Get the incoming JSON data
    data = request.get_json()
    if not data:
        return "No JSON data received", 400
    
    # Generate a filename with the current timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    prefix = f"{timestamp}-{random.randint(1000, 10000)}"
    filename = f"{prefix}-event.txt"
    
    # Save the JSON data to a file
    with open(filename, 'w') as file:
        json.dump(data, file)

    event = data
    event_parser = FigmaEventParser(event, figma_api)

    created = event_parser.created_components()
    modified = event_parser.modified_components()

    if 'file_key' in event:
        message = generate_report(event, created['components'], modified['components'])
        with open("{prefix}-message.txt", "w") as w:
            w.write(message)

        CODEX_BOT_TOKEN = os.environ.get('CODEX_BOT_TOKEN', None)
        if CODEX_BOT_TOKEN is not None:
            requests.post(f"https://notify.bot.codex.so/u/{CODEX_BOT_TOKEN}", data={
                "message": message,
                "parse_mode": "HTML"
            })
    
    return "JSON data saved", 200


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=80)
