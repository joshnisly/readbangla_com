#!/usr/bin/python
# pylint: disable=W0212

if __name__ != '__main__':
    import django
    import django.db
    import app.models

import os
import re
import sys


# ___Database schema upgrades___
# swatdb will attempt to automatically modify the database to
# match the specified schema. If data loss is involved (i.e. dropping
# a column or table), swatdb will refuse to do so unless upgrade
# hints are specified.

# This class will be passed to the upgrade_hints() function.
class UpgradeHints(object):
    def __init__(self):
        # If either point to None, it means the table is dropped
        self._table_adjustments = {} # Table name to new name/delete
        self._col_adjustments = {} # Table name to dict of col adjustments

    def drop_table(self, name):
        assert not name in self._table_adjustments
        self._table_adjustments[name] = None

    def rename_table(self, old_name, new_name):
        assert not old_name in self._table_adjustments
        assert new_name is not None
        self._table_adjustments[old_name] = new_name

    def drop_column(self, table, name):
        adj = self._col_adjustments.setdefault(table, {})
        adj[name] = None

    def rename_column(self, table, old_name, new_name):
        adj = self._col_adjustments.setdefault(table, {})
        adj[old_name] = new_name

# API to swatdb.Database
class UpgradeError(Exception):
    pass

class DatabaseUpgrader(object):
    def __init__(self, db_name, app_name):
        self._conn = django.db.connection
        self._db_name = db_name
        self._app_name = app_name

        self._changes = None

    def get_changes(self):
        if self._changes is None:
            hints = _InternalUpgradeHints()
            #TODO:if hasattr(self._new_schema, 'upgrade_hints'):
            #    self._new_schema.upgrade_hints(hints)
            db_def = self._build_def_from_sql()
            new_def = self._build_def_from_models()
            self._changes = self._calc_changes(db_def, new_def,
                                               hints)
        return self._changes

    def make_changes(self):
        for change in self.get_changes():
            if change['type'] == 'add_table':
                self._add_table(change['name'], change['def'])
            elif change['type'] == 'delete_table':
                self._drop_table(change['name'])
            elif change['type'] == 'rename_table':
                self._rename_table(change['old_name'], change['new_name'])
            elif change['type'] == 'add_col':
                self._add_col(change['table'], change['def'])
            elif change['type'] == 'delete_col':
                self._delete_col(change['table'], change['name'])
            elif change['type'] == 'rename_col':
                self._change_col(change['table'], change['old_name'],
                                 change['def'])
            elif change['type'] == 'change_col':
                self._change_col(change['table'], change['name'],
                                 change['def'])
            elif change['type'] == 'make_unique':
                self._make_col_unique(change['table'], change['name'],
                                      change['is_unique'])

    # INTERNALS
    # CHANGE CALCULATION
    def _calc_changes(self, db_def, new_def, upgrade_hints):
        changes = []
        for old_table in db_def:
            new_table = upgrade_hints.get_new_table_name(old_table)
            
            if new_table is None:
                # Check table deletes
                changes.append({
                    'type': 'delete_table',
                    'name': old_table
                })
                continue
            elif old_table != new_table:
                # Check for table rename
                changes.append({
                    'type': 'rename_table',
                    'old_name': old_table,
                    'new_name': new_table
                })
            elif not new_table in new_def:
                error = 'Table %s no longer appears, ' % new_table + \
                        'but is not marked for deletion.'
                raise UpgradeError, error

            for old_col in db_def[old_table]['fields']:
                old_col_name = old_col['name']
                new_col_name = upgrade_hints.get_new_col_name(new_table, old_col_name)

                # Col renames
                new_col = None
                if not new_col_name is None:
                    new_col = filter(lambda x: x['name'] == new_col_name,
                                     new_def[new_table]['fields'])
                    new_col = new_col[0] if new_col else None
                    if new_col is None:
                        raise UpgradeError, 'Column is not defined: %s.%s' % \
                            (new_table, new_col_name)

                # Check col deletes
                if new_col_name is None:
                    changes.append({
                        'type': 'delete_col',
                        'table': old_table,
                        'name': old_col_name
                    })
                    continue
                elif new_col_name != old_col_name:
                    changes.append({
                        'type': 'rename_col',
                        'table': new_table,
                        'old_name': old_col_name,
                        'new_name': new_col_name,
                        'def': self._get_col_from_db_def(new_col)
                    })
                else:
                    new_col_names = [x['name'] for x in new_def[new_table]['fields']]
                    if not new_col_name in new_col_names:
                        error = 'Col %s.%s no longer appears, ' + \
                                'but is not marked for deletion.'
                        raise UpgradeError, error % (new_table, old_col_name)

                # Check col modifications
                if old_col['type'] != self._get_sql_col_type(new_col['type']) and \
                    not (old_col['type'] == 'blob' and new_col['type'] == 'file'):

                    print old_col['type'], new_col['type'], self._get_sql_col_type(new_col['type'])
                    error = '%s.%s: changing column types is not supported.'
                    raise UpgradeError, error % (new_table, new_col['name'])

                if old_col.get('length') != self._get_sql_col_length(new_col):
                    changes.append({
                        'type': 'change_col',
                        'table': new_table,
                        'name': new_col['name'],
                        'def': self._get_col_from_db_def(new_col)
                    })

                if old_col.get('unique') != new_col.get('unique'):
                    changes.append({
                        'type': 'make_unique',
                        'table': new_table,
                        'name': new_col['name'],
                        'is_unique': new_col.get('unique', False)
                    })

            # Check for col additions
            old_col_names = [x['name'] for x in db_def[old_table]['fields']]
            for new_col in new_def[new_table]['fields']:
                new_col_name = new_col['name']
                old_col_name = upgrade_hints.get_old_col_name(new_table,
                                                              new_col_name)
                if not old_col_name in old_col_names and \
                        not new_col_name in old_col_names:
                    changes.append({
                        'type': 'add_col',
                        'table': new_table,
                        'def': self._get_col_from_db_def(new_col)
                    })

        for new_table in new_def:
            old_table = upgrade_hints.get_old_table_name(new_table)
            if not old_table in db_def and not new_table in db_def:
                changes.append({
                    'type': 'add_table',
                    'name': new_table,
                    'def': self._get_table_from_db_def(new_def[new_table])
                })
                continue

            
        return changes

    def _build_def_from_models(self):
        db_def = {}

        models = django.db.models.get_models()
        models = filter(lambda x: x.__module__.startswith(self._app_name + '.'), models)
        for model in models:
            table_def = {
                'primary_key': ('id',),
                'fields': []
            }
            table_name = '%s_%s' % (self._app_name, model.__name__.lower())
            for field in model._meta.fields:
                field_type = field.db_type()
                auto_increment = False
                if field_type.endswith('AUTO_INCREMENT'):
                    field_type = field_type[:-len('AUTO_INCREMENT')].strip()
                    auto_increment = True
                field_type = field_type.replace('integer', 'int')
                if '(' in field_type:
                    field_type = field_type.split('(')[0]

                table_def['fields'].append({
                    'name': field.column,
                    'type': field_type,
                    'length': field.max_length,
                })

                if auto_increment:
                    table_def['fields'][-1]['auto_increment'] = True

                if field._unique:
                    table_def['fields'][-1]['unique'] = True

            db_def[table_name] = table_def

        return db_def

    def _build_def_from_sql(self):
        db_def = {}
        tables = self._getalltables()
        for table in tables:
            if not table.lower().startswith(self._app_name):
                continue
            table_def = {
                'primary_key': ('id',),
                'fields': []
            }
            for field in self._get_table_field_names(table):
                field_def = self._get_field_def(table, field)
                table_def['fields'].append(field_def)
            db_def[table] = table_def

        return db_def

    def _get_table_field_names(self, table):
        query = 'SHOW COLUMNS from %s' % self._escapename(table)
        col_names = [x[0] for x in self._cur_query(query)]
        return col_names

    def _get_field_def(self, table, field):
        query = 'SHOW COLUMNS from %s' % self._escapename(table)
        col = filter(lambda x: x[0] == field, self._cur_query(query))[0]

        length_re = re.compile('\((\d+)\)')
        length_match = length_re.search(col[1])
        length = length_match.group(1) if length_match else None

        field_def = {
            'name': col[0],
            'type': length_re.sub('', col[1]),
        }
        if field_def['type'] in _VARLEN_DATA_TYPES:
            field_def['length'] = int(length)
        if col[5]:
            field_def['auto_increment'] = True
        if self._is_col_unique(table, field_def['name']):
            field_def['unique'] = True

        return field_def

    def _get_table_from_db_def(self, table):
        table = dict(table)
        if 'format_expr' in table:
            del table['format_expr']
        table['fields'] = [self._get_col_from_db_def(x) \
                           for x in table['fields']]
        return table

    def _get_col_from_db_def(self, col):
        col = dict(col)
        if 'label' in col:
            del col['label']
        return col

    def _is_col_unique(self, table, col):
        sql = 'SELECT NON_UNIQUE FROM INFORMATION_SCHEMA.STATISTICS ' + \
             'WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND INDEX_NAME = %s;' % (
            self._escapestring(self._db_name),
            self._escapestring(table),
            self._escapestring(col)
        )
        results = list(self._cur_query(sql))
        if len(results) == 1:
            assert len(results[0]) == 1
            return not results[0][0]
        return False

    # DATABASE MODIFICATION
    def _add_table(self, table, table_def):
        # Generate the column definitions.
        colsql = []
        for fielddef in table_def['fields']:
            colsql.append(self._get_sql_for_field(fielddef, True))
        colsql.append('PRIMARY KEY (%s)' % ', '.join(self._escapename(name) \
                for name in table_def['primary_key']))

        sql = 'CREATE TABLE %s (\n' % self._escapename(table)
        sql += '  %s' % ',\n  '.join(colsql)
        sql += '\n);'
        self._cmd_query(sql)

    def _rename_table(self, old_name, new_name):
        sql = 'ALTER TABLE %s RENAME TO %s;' % (
            self._escapename(old_name),
            self._escapename(new_name),
        )
        self._cmd_query(sql)

    def _get_sql_col_type(self, def_type):
        if def_type in _RELATIONSHIP_TYPES:
            return 'int'
        elif def_type == 'bool':
            return 'tinyint'
        elif def_type == 'boolean':
            return 'tinyint'
        elif def_type == 'file':
            return 'varchar'
        elif def_type == 'currency':
            return 'float'
        return def_type

    def _get_sql_col_length(self, fielddef):
        if fielddef['type'] == 'file':
            return db_file._FIELDLEN
        return fielddef.get('length')

    def _get_sql_for_field(self, fielddef, include_unique):
        name = fielddef['name']

        data_type = self._get_sql_col_type(fielddef['type'])
        length = self._get_sql_col_length(fielddef)
        if not length is None:
            data_type += '(%s)' % length
        
        extras = ''
        if fielddef.get('auto_increment'):
            extras += ' AUTO_INCREMENT'
        
        sql = '%s %s%s' % (self._escapename(name), data_type, extras)
        if fielddef.get('unique') and include_unique:
            sql += ',\n UNIQUE (%s)' % self._escapename(name)
        return sql

    def _add_col(self, table, col_def):
        sql = 'ALTER TABLE %s ADD COLUMN %s;' % (
            self._escapename(table),
            self._get_sql_for_field(col_def, False)
        )
        self._cmd_query(sql)

        if col_def.get('unique'):
            self._make_col_unique(table, col_def['name'], True)

    def _drop_table(self, table):
        sql = 'DROP TABLE %s;' % self._escapename(table)
        self._cmd_query(sql)

    def _delete_col(self, table, col_name):
        sql = 'ALTER TABLE %s DROP COLUMN %s;' % (
            self._escapename(table),
            self._escapename(col_name),
        )
        self._cmd_query(sql)

    def _change_col(self, table, old_name, new_def):
        sql = 'ALTER TABLE %s CHANGE COLUMN %s %s;' % (
            self._escapename(table),
            self._escapename(old_name),
            self._get_sql_for_field(new_def, False)
        )
        self._cmd_query(sql)

    def _make_col_unique(self, table, name, is_unique):
        if is_unique:
            sql = 'ALTER TABLE %s ADD UNIQUE (%s);' % (
                self._escapename(table),
                self._escapename(name)
            )
        else:
            sql = 'ALTER TABLE %s DROP INDEX %s;' % (
                self._escapename(table),
                self._escapename(name)
            )
        self._cmd_query(sql)

    def _escapestring(self, value):
        orig_value = value
        value = unicode(value).replace('\\', '\\\\')
        for character, escape in _CHARACTER_ESCAPES.items():
            value = value.replace(character, escape)
        # Single-quoting is better because of ANSI_QUOTES setting.
        value = "'%s'" % value
        #assert cls._unescapestring(value) == orig_value
        return value

    def _escapename(self, name):
        if '`' in name:
            raise DatabaseError, 'Invalid SQL name: %s' % name
        # Force names to lower case to avoid case sensitivity differences
        # on Windows/Unix
        assert name == name.lower()
        return '.'.join(["`%s`" % x for x in name.split('.')])

    def _getalltables(self):
        sql = """ SHOW FULL TABLES IN %s
                  WHERE Table_type = "BASE TABLE";
              """ % self._escapename(self._db_name)
        return sorted(result[0] for result in self._cur_query(sql))

    def _cur_query(self, sql):
        """ Yields tuples.
        """
        # TODO: Wrap exception
        cursor = self._conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def _cmd_query(self, sql):
        self._conn.cursor().execute(sql)

_RELATIONSHIP_TYPES = ('foreign_key',)
_CHARACTER_ESCAPES = { # excludes \\
    '\0': r'\0',
    "'": r"\'",
    '"': r'\"',
    '\b': r'\b',
    '\n': r'\n',
    '\r': r'\r',
    '\t': r'\t',
    '\x1A': r'\Z', # windows EOF
    #'%': r'\%', todo: only for "like" keyword?
    #'_': r'\_',
}

_VARLEN_DATA_TYPES = ('varchar',)
_DATA_TYPES = _VARLEN_DATA_TYPES + (
    'int',
    'enum',
    'date',
    'text',
    'blob',
    'boolean',
    'float',
    'file',
    'currency',
)


# This is an internal class to allow the DatabaseUpgrader
# to have internal functions without cluttering up the API.
class _InternalUpgradeHints(UpgradeHints):
    def get_new_table_name(self, old_table):
        return self._table_adjustments.get(old_table, old_table)

    def get_old_table_name(self, new_table):
        for key, value in self._table_adjustments.iteritems():
            if value == new_table:
                return key
        return new_table

    def get_new_col_name(self, table, old_col):
        return self._col_adjustments.get(table, {}).get(old_col, old_col)

    def get_old_col_name(self, table, new_col):
        if not table in self._col_adjustments:
            return new_col

        for key, value in self._col_adjustments[table].iteritems():
            if value == new_col:
                return key
        return new_col

if __name__ == '__main__':
    PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
    path = os.path.dirname(PARENT_DIR)
    sys.path.insert(0, path)

    import django.core.management

    import settings
    django.core.management.setup_environ(settings)

    import app.models

    import django
    import django.db

    import json

    upgrader = DatabaseUpgrader('bangla_dict', 'app')

    if upgrader.get_changes():
        print json.dumps(upgrader.get_changes(), indent=3)
        print 'Do you want to make these changes [Y/N]?',
        if raw_input().lower() == 'y':
            upgrader.make_changes()
    else:
        print 'No changes detected.'

