#!/usr/bin/env python3
import json, os, sys

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'custom-rules.json')

def respond(data, status=200):
    sys.stdout.write("Status: {}\r\n".format(status))
    sys.stdout.write("Content-Type: application/json\r\n\r\n")
    sys.stdout.write(json.dumps(data))
    sys.stdout.flush()

if os.environ.get('REQUEST_METHOD') != 'POST':
    respond({"error": "Method not allowed"}, 405)
    sys.exit()

try:
    length = int(os.environ.get('CONTENT_LENGTH', 0))
    body = sys.stdin.buffer.read(length).decode('utf-8')
    rules = json.loads(body)
except Exception as e:
    respond({"error": "Invalid JSON: " + str(e)}, 400)
    sys.exit()

if not isinstance(rules, list):
    respond({"error": "Expected a JSON array"}, 400)
    sys.exit()

for r in rules:
    if not r.get('id') or not r.get('name'):
        respond({"error": "Each rule must have id and name"}, 400)
        sys.exit()

try:
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)
    respond({"success": True})
except Exception as e:
    respond({"error": "Failed to write file: " + str(e)}, 500)
