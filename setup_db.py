import sqlite3
import csv
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, 'data', 'routes.db')

FILES = [
    ('46809', os.path.join(BASE, 'data', 'carrier_routes_46809_extracted.csv')),
    ('46819', os.path.join(BASE, 'data', 'carrier_routes_46819_extracted.cvs.csv')),
]

def setup():
    conn = sqlite3.connect(DB_PATH)

    conn.execute('''
        CREATE TABLE IF NOT EXISTS routes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            zip_code    TEXT    NOT NULL,
            street_name TEXT    NOT NULL,
            range_start INTEGER NOT NULL,
            range_end   INTEGER NOT NULL,
            even_odd    TEXT,
            carrier     TEXT    NOT NULL
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_street ON routes(LOWER(street_name))')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_range  ON routes(range_start, range_end)')
    conn.execute('DELETE FROM routes')

    # Glastonbury is a special case: any address goes to route 98
    conn.execute(
        'INSERT INTO routes (zip_code, street_name, range_start, range_end, even_odd, carrier) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        ('46809', 'GLASTONBURY', 1, 99999, None, '98')
    )

    total = 1
    for zip_code, path in FILES:
        with open(path, newline='') as f:
            next(f)  # skip title line ("carrier_routes_46809_extracted")
            reader = csv.DictReader(f)
            for row in reader:
                conn.execute(
                    'INSERT INTO routes '
                    '(zip_code, street_name, range_start, range_end, even_odd, carrier) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (
                        zip_code,
                        row['street_name'].strip().upper(),
                        int(row['range_start']),
                        int(row['range_end']),
                        row['even_odd'].strip() or None,
                        row['carrier_number'].strip(),
                    )
                )
                total += 1

    conn.commit()
    count = conn.execute('SELECT COUNT(*) FROM routes').fetchone()[0]
    print(f'Done — {count} route entries loaded.')
    conn.close()

if __name__ == '__main__':
    setup()
