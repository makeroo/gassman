from gassman import ioc

with ioc.db_connection().connection() as cur:
    cur.execute(
        '''SELECT p.id
             FROM person p
        LEFT JOIN account_person ap ON ap.person_id = p.id
            WHERE ap.id IS NULL
            LIMIT 1''',
        []
    )
    pid = cur.fetchone()[0]
    print('Person not belonging to a CSA:', pid)

    cur.execute(
        '''SELECT x.person_id
             FROM account_person x
        LEFT JOIN permission_grant g ON g.person_id = x.person_id
            WHERE x.account_id IN (SELECT ap.account_id
                                     FROM account_person ap
                                    WHERE ap.to_date IS NULL
                                 GROUP BY ap.account_id
                                   HAVING COUNT(ap.person_id) = 1
                                   )
                  AND
                  g.id IS NULL
            LIMIT 1''',
        []
    )
    pid = cur.fetchone()[0]
    print('Person with no permissions and single owned account:', pid)

    cur.execute(
        '''SELECT x.person_id
             FROM account_person x
        LEFT JOIN permission_grant g ON g.person_id = x.person_id
            WHERE x.account_id IN (SELECT ap.account_id
                                     FROM account_person ap
                                    WHERE ap.to_date IS NULL
                                 GROUP BY ap.account_id
                                   HAVING COUNT(ap.person_id) > 1
                                   )
                  AND
                  g.id IS NULL
            LIMIT 1''',
        []
    )
    pid = cur.fetchone()[0]
    print('Person with no permissions and multi-owned account:', pid)

    cur.execute(
        '''SELECT x.person_id
             FROM account_person x
        LEFT JOIN permission_grant g ON g.person_id = x.person_id
            WHERE x.account_id IN (SELECT ap.account_id
                                     FROM account_person ap
                                    WHERE ap.to_date IS NOT NULL
                                 GROUP BY ap.account_id
                                   HAVING COUNT(ap.person_id) = 1
                                   )
                  AND
                  g.id IS NULL
            LIMIT 1''',
        []
    )
    pid = cur.fetchone()[0]
    print('Person with no permissions and belonging to a CSA no more:', pid)

    cur.execute(
        '''SELECT p.id
            FROM person p
           WHERE p.id IN (SELECT g2.person_id
                            FROM permission_grant g2
                           WHERE g2.perm_id = 2)
                 AND
                 p.id NOT IN (SELECT g9.person_id
                                FROM permission_grant g9
                               WHERE g9.perm_id = 9)
           LIMIT 1''',
        []
    )
    pid = cur.fetchone()[0]
    print('Person with can_check_accounts permission only:', pid)

    cur.execute(
        '''SELECT p.id
            FROM person p
           WHERE p.id NOT IN (SELECT g2.person_id
                            FROM permission_grant g2
                           WHERE g2.perm_id = 2)
                 AND
                 p.id IN (SELECT g9.person_id
                                FROM permission_grant g9
                               WHERE g9.perm_id = 9)
           LIMIT 1''',
        []
    )
    pid = cur.fetchone()[0]
    print('Person with can_view_contacts permission only:', pid)

    cur.execute(
        '''SELECT p.id
             FROM person p
             JOIN permission_grant g1 ON p.id = g1.person_id
             JOIN permission_grant g2 ON p.id = g2.person_id
            WHERE g1.perm_id = 2
                  AND
                  g2.perm_id = 9
                  AND
                  g1.csa_id = g2.csa_id
            LIMIT 1''',
        []
    )
    pid = cur.fetchone()[0]
    print('Person with can_view_contacts and can_check_accounts permissions:', pid)
