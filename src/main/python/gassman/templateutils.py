def member_name(profile):
    fn = profile.get('first_name')
    mn = profile.get('middle_name')
    ln = profile.get('last_name')
    return (fn + (' ' + mn if mn else '') + (' ' + ln if ln else '')).strip()


def shortDate(d):
    return d.strftime('%Y/%m/%d') # FIXME il formato dipende dal locale dell'utente


def pubDate(d):
    return d.strftime('%a, %d %b %Y %H:%M:%S GMT')


def currency(v, sym):
    return '%s%s' % (v, sym)
