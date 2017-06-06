from . import JsonBaseHandler, GDataException

import error_codes


class OrdersOrderHandler (JsonBaseHandler):
    def do(self, cur):
        order_id = self.payload['order_id']
        uid = self.current_user

        if uid is None:
            raise GDataException(error_codes.E_not_authenticated, 401)

        # autorizzazioni:
        # un permesso può essere visto da tutti i membri di un gas
        #  purché non sia draft
        # se è draft può essere visto solo da i membri del gas che hanno permesso canPlaceOrders

        q, a = self.application.conn.sql_factory.order_fetch(order_id)
        cur.execute(q, a)

        r = self.application.conn.sql_factory.fetch_object(cur)

        if r is None:
            return None

        csa_id = r['csa_id']
        state = r['state']

        if not(
                self.application.has_permission_by_csa(
                    cur, self.application.conn.sql_factory.P_canPlaceOrders, uid, csa_id
                ) if state != self.application.conn.sql_factory.Os_draft else
                self.application.is_member_of_csa(cur, uid, csa_id, False)
        ):
            raise GDataException(error_codes.E_permission_denied, 403)

        q, a = self.application.conn.sql_factory.order_delivery(order_id)
        cur.execute(q, a)
        r['delivery'] = self.application.conn.sql_factory.fetch_object(cur)

        q, a = self.application.conn.sql_factory.order_products(order_id)
        cur.execute(q, a)
        products_array = self.application.conn.sql_factory.iter_objects(cur)

        r['products'] = products_array

        if products_array:
            products_index = {
                p['id']: p
                for p in products_array
            }

            q, a = self.application.conn.sql_factory.order_product_quantities(order_id)
            cur.execute(q, a)

            for q in self.application.conn.sql_factory.iter_objects(cur):
                p = products_index[q['product']]
                p.setdefault('quantities', []).append(q)

        return r


class OrdersSaveDraft (JsonBaseHandler):
    def do(self, cur):
        order_draft = self.payload
        uid = self.current_user

        if uid is None:
            raise GDataException(error_codes.E_not_authenticated, 401)

        try:
            order_id = order_draft['id']
            csa_id = order_draft['csa_id']

            if order_draft['profile_required'] not in ('Y', 'N'):
                raise GDataException(error_codes.E_illegal_payload)

            for p in order_draft['products']:
                for q in p['quantities']:
                    amount = q['amount']
                    if amount is not None and type(amount) != str:
                        raise GDataException(error_codes.E_illegal_amount)

                    if float(amount) < 0.0:
                        raise GDataException(error_codes.E_illegal_amount)
        except KeyError:
            raise GDataException(error_codes.E_illegal_payload)
        except ValueError:
            raise GDataException(error_codes.E_illegal_amount)

        if not self.application.has_permission_by_csa(
                    cur, self.application.conn.sql_factory.P_canPlaceOrders, uid, csa_id
                ):
            raise GDataException(error_codes.E_permission_denied, 403)

        if order_id is None:
            # nuovo ordine
            q, a = self.application.conn.sql_factory.order_save_draft(order_draft)
            cur.execute(q, a)
            order_id = cur.lastrowid
        else:
            # aggiornamento ordine
            q, a = self.application.conn.sql_factory.order_update_draft(order_draft)
            cur.execute(q, a)
            if cur.rowcount != 1:
                raise GDataException(error_codes.E_illegal_order)

            q, a = self.application.conn.sql_factory.order_cleanup_products(order_id)
            cur.execute(q, a)

        try:
            products = order_draft['products']
            for p, idx in zip(products, range(len(products))):
                quantities = p['quantities']

                q, a = self.application.conn.sql_factory.order_insert_product(
                    order_id, idx, p
                )
                cur.execute(q, a)
                product_id = cur.lastrowid

                for q, qidx in zip(quantities, range(len(quantities))):
                    q, a = self.application.conn.sql_factory.order_insert_product_quantity(
                        product_id, idx, q
                    )
                    cur.execute(q, a)
        except (KeyError, TypeError):
            raise GDataException(error_codes.E_illegal_payload)

        return [order_id]
