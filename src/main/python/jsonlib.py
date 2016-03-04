"""
Raccolta di codice per la manipolazione del JSON.

La libreria offre funzionalità di conversione da e per JSON.

 dell'I/O fra client e server,
ovvero codifica JSON e compressione gzip.

@author: makeroo
"""

import json
import datetime
import decimal


def encode_decimal(v):
    return None if v is None else str(v)


def decode_decimal(s):
    return None if empty_value(s) else decimal.Decimal(s)


def encode_time(v):
    return None if v is None else v.strftime('%H:%M:%S.%f')


def decode_time(s):
    return None if empty_value(s) else datetime.datetime.strptime(s, '%H:%M:%S.%f').time()


def encode_date(v):
    return None if v is None else v.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def decode_date(s):
    if empty_value(s):
        return None
    try:
        return datetime.datetime.strptime(s[:-1], '%Y-%m-%dT%H:%M:%S.%f')  # 24
    except ValueError:
        return datetime.datetime.strptime(s[:-1], '%Y-%m-%dT%H:%M:%S')  # 20


def encode_timedelta(v):
    return None if v is None else v.total_seconds()


def decode_timedelta(v):
    return None if empty_value(v) else datetime.timedelta(0, float(v))


def encode_set(v):
    return None if empty_value(v) else list(v)


def empty_value(v):
    return v is None or (type(v) == str and len(v) == 0)


class ExtendedJSONEncoder (json.JSONEncoder):
    encodings = {
        datetime.date: encode_date,
        datetime.datetime: encode_date,
        datetime.time: encode_time,
        datetime.timedelta: encode_timedelta,
        decimal.Decimal: encode_decimal,
        set: encode_set,
    }

    def default_object_encoding(self, o):
        try:
            return vars(o)
        except TypeError:
            return super(ExtendedJSONEncoder, self).default(o)

    def default(self, o):
        return self.encodings.get(type(o), self.default_object_encoding)(o)


def to_json(obj, encoder=ExtendedJSONEncoder()):
    if obj is None:
        return ''
    return json.dumps(obj, default=encoder.default)


def write_json(obj, fh, encoder=ExtendedJSONEncoder()):
    if obj is None:
        return
    return json.dump(obj, fh, default=encoder.default)
