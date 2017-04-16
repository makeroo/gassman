import logging

from . import JsonBaseHandler, GDataException

import error_codes


log_gassman = logging.getLogger('gassman.backend')


class EventSaveHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        log_gassman.debug('saving: %s', p)
        event_id = p.get('id')
        shifts = p.pop('shifts')

        if not self.application.has_permission_by_csa(cur, self.application.conn.sql_factory.P_canManageShifts, uid, csa_id):
            raise GDataException(error_codes.E_permission_denied, 403)

        if event_id is not None:
            cur.execute(*self.application.conn.sql_factory.csa_delivery_date_check(csa_id, event_id))
            v = cur.fetchone()[0]
            if v == 0:
                raise GDataException(error_codes.E_permission_denied, 403)
            cur.execute(*self.application.conn.sql_factory.csa_delivery_date_update(**p))
            cur.execute(*self.application.conn.sql_factory.csa_delivery_shift_remove_all(event_id))
        else:
            cur.execute(*self.application.conn.sql_factory.csa_delivery_place_check(csa_id, p['delivery_place_id']))
            v = cur.fetchone()[0]
            if v == 0:
                raise GDataException(error_codes.E_permission_denied, 403)
            cur.execute(*self.application.conn.sql_factory.csa_delivery_date_save(**p))
            event_id = cur.lastrowid
        for shift in shifts:
            shift['delivery_date_id'] = event_id
            cur.execute(*self.application.conn.sql_factory.csa_delivery_shift_add(shift))
        return {
            'id': event_id
        }


class EventRemoveHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        log_gassman.debug('removing: %s', p)

        if not self.application.has_permission_by_csa(cur, self.application.conn.sql_factory.P_canManageShifts, uid, csa_id):
            raise GDataException(error_codes.E_permission_denied, 403)

        date_id = p['id']
        cur.execute(*self.application.conn.sql_factory.csa_delivery_date_check(csa_id, date_id))
        v = cur.fetchone()[0]
        if v == 0:
            raise GDataException(error_codes.E_permission_denied, 403)

        cur.execute(*self.application.conn.sql_factory.csa_delivery_shift_remove_all(date_id))
        cur.execute(*self.application.conn.sql_factory.csa_delivery_date_remove(date_id))
