'''
Created on 30/set/2014

@author: makeroo
'''

import json
import base64

def extract_payload_from_oauth2_id_token (id_token):
    '''Estraggo l'attributo email dal token id OAuth2.
    Non faccio alcuna verifica perché si assume che il token sia stato
    appena ricevuto da google.
    '''
    _body_sign, p, _signature = id_token.split('.')
    # Guard against unicode strings, which base64 can't handle.
    pbytes = p.encode('ascii')
    padded = pbytes + b'=' * (4 - len(pbytes) % 4)
    json_bytes = base64.urlsafe_b64decode(padded)
    json_str = str(json_bytes, 'utf-8')
    return json.loads(json_str)
