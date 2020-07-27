# https://github.com/tchellomello/python-ring-doorbell
import json
import getpass
import os
from pathlib import Path
from pprint import pprint

from ring_doorbell import Ring, Auth
from oauthlib.oauth2 import MissingTokenError

cache_file = Path("test_token.cache")

# grab info on this many videos at a time
CHUNK_SIZE = 50

def _format_filename(event):
    if not isinstance(event, dict):
        return

    if event["answered"]:
        answered_status = "answered"
    else:
        answered_status = "not_answered"

    filename = "{}_{}_{}_{}".format(
        event["created_at"], event["kind"], answered_status, event["id"]
    )

    filename = filename.replace(" ", "_").replace(":", ".") + ".mp4"
    return filename

def download(deck):
	count = 0

	all_events = deck.history(limit=100)
	total = len(all_events);
	last_eid = all_events[-1]['id']

	while True:
		next_events = deck.history(older_than=last_eid, limit=CHUNK_SIZE)
		if next_events:
			next_last_eid = next_events[-1]['id'];
			if next_last_eid == last_eid:
				break;
			else:
				total += len(next_events);
				last_eid = next_last_eid;
		else:
			break;

	print ('Total number of events is at least %s' % (total))

	eid = None

	while True:
		events = deck.history(older_than=eid, limit=CHUNK_SIZE)
		for event in events:
			eid = event['id']
			if eid < last_eid:
				return

			filename = _format_filename(event)
			fq_filename = 'videos/{}'.format(filename)

			if not os.path.isfile(fq_filename):
				try:
					deck.recording_download(eid, filename=fq_filename)
				except Exception as inst:
					print('The file ' + fq_filename + ' could not be downloaded.')
			else:
				print('The file ' + fq_filename + ' already exists.')
			count += 1
			print ('%s %s:%s' % (count, eid, filename))

def token_updated(token):
	cache_file.write_text(json.dumps(token))

def otp_callback():
	auth_code = input("2FA code: ")
	return auth_code

def main():
    if cache_file.is_file():
        auth = Auth("MyProject/1.0", json.loads(cache_file.read_text()), token_updated)
    else:
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        auth = Auth("MyProject/1.0", None, token_updated)
        try:
            auth.fetch_token(username, password)
        except MissingTokenError:
            auth.fetch_token(username, password, otp_callback())

    ring = Ring(auth)
    ring.update_data()

    devices = ring.devices()
    pprint(devices)

    # play with the API to figure out which camera you want
    deck = devices['doorbots'][0]
    download(deck)
    print ('\nDONE.')

if __name__ == "__main__":
    main()
