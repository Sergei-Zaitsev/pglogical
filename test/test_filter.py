import random
import string
import unittest
from base import PGLogicalOutputTest

class FilterTest(PGLogicalOutputTest):
    def rand_string(self, length):
        return ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(length)])

    def set_up(self):
        cur = self.conn.cursor()
        cur.execute("CREATE TABLE test_changes (cola serial PRIMARY KEY, colb timestamptz default now(), colc text);")
        cur.execute("CREATE TABLE test_changes_filter (cola serial PRIMARY KEY, colb timestamptz default now(), colc text);")
        cur.execute("CREATE FUNCTION test_filter(nodeid text, relid oid, action \"char\") returns bool AS $$BEGIN RETURN relid::regclass::text LIKE '%_filter%'; END$$ STABLE LANGUAGE plpgsql;")
        self.conn.commit()
        # empty the slot
        self.get_changes().next()

    def tear_down(self):
        cur = self.conn.cursor()
        cur.execute("DROP TABLE test_changes;")
        cur.execute("DROP TABLE test_changes_filter;")
        cur.execute("DROP FUNCTION test_filter(text, oid, \"char\")");
        self.conn.commit()

    def test_filter(self):

        cur = self.conn.cursor()
        cur.execute("INSERT INTO test_changes(colb, colc) VALUES(%s, %s)", ('2015-08-08', 'foobar'))
        cur.execute("INSERT INTO test_changes_filter(colb, colc) VALUES(%s, %s)", ('2015-08-08', 'foobar'))
        cur.execute("INSERT INTO test_changes(colb, colc) VALUES(%s, %s)", ('2015-08-08', 'bazbar'))
        self.conn.commit()

        cur.execute("INSERT INTO test_changes_filter(colb, colc) VALUES(%s, %s)", ('2015-08-08', 'bazbar'))
        self.conn.commit()

        messages = self.get_changes({'hooks.table_change_filter': 'public.test_filter', 'node_id': 'foo'})

        # two inserts into test_changes, the test_changes_filter insert is filtered out
        m = messages.next()
        self.assertEqual(m.mesage_type, 'B')
        m = messages.next()
        self.assertEqual(m.mesage_type, 'R')
        m = messages.next()
        self.assertEqual(m.mesage_type, 'I')
        self.assertEqual(m.message['newtup'][2], 'foobar')
        m = messages.next()
        self.assertEqual(m.mesage_type, 'R')
        m = messages.next()
        self.assertEqual(m.mesage_type, 'I')
        self.assertEqual(m.message['newtup'][2], 'bazbar')
        m = messages.next()
        self.assertEqual(m.mesage_type, 'C')

        # just empty tx test_changes_filter insert is filtered out
        m = messages.next()
        self.assertEqual(m.mesage_type, 'B')
        m = messages.next()
        self.assertEqual(m.mesage_type, 'C')

    def test_validation(self):
        with self.assertRaises(Exception):
            self.get_changes({'hooks.table_change_filter': 'public.test_filter'}).next()
        with self.assertRaises(Exception):
            self.get_changes({'hooks.table_change_filter': 'public.foobar'}).next()


if __name__ == '__main__':
    unittest.main()
