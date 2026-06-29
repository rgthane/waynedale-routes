import re
import sqlite3
import os
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'routes.db')

DIRECTION_MAP = {'north': 'N', 'south': 'S', 'east': 'E', 'west': 'W',
                 'n': 'N', 's': 'S', 'w': 'W'}
PARITY_MAP    = {'even': 'E', 'odd': 'O', 'e': 'E', 'o': 'O'}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def parse_query(raw):
    # "78 hundred" -> "7800"
    text = re.sub(r'\b(\d+)\s+hundred\b', lambda m: str(int(m.group(1)) * 100), raw.lower())

    number       = None
    is_block     = False   # True when user typed a short number (43 → 4300 block)
    direction    = None
    parity       = None
    street_words = []

    for token in text.split():
        if re.match(r'^\d+$', token):
            n = int(token)
            if len(token) <= 2:          # "43" → search 4300-4399 block
                number   = n * 100
                is_block = True
            else:                        # "4300" or "4301" → exact address
                number   = n
                is_block = False
        elif token in PARITY_MAP:
            parity = PARITY_MAP[token]
        elif token in DIRECTION_MAP:
            direction = DIRECTION_MAP[token]
        else:
            street_words.append(token)

    return number, is_block, direction, parity, street_words

def search(raw):
    if not raw.strip():
        return []

    number, is_block, direction, parity, street_words = parse_query(raw)

    conditions, params = [], []

    if number is not None:
        if is_block:
            # Overlap with the hundred block (e.g. 4300–4399)
            conditions.append('range_start <= ? AND range_end >= ?')
            params += [number + 99, number]
        else:
            conditions.append('range_start <= ? AND range_end >= ?')
            params += [number, number]

    # Parity: explicit (E/O/even/odd) wins;
    # for exact addresses auto-detect from even/odd of the number;
    # block searches get no auto-parity (block spans both).
    if parity:
        conditions.append("(even_odd IS NULL OR even_odd = '' OR even_odd = ?)")
        params.append(parity)
    elif number is not None and not is_block:
        auto = 'E' if number % 2 == 0 else 'O'
        conditions.append("(even_odd IS NULL OR even_odd = '' OR even_odd = ?)")
        params.append(auto)

    if direction:
        conditions.append('(UPPER(street_name) LIKE ? OR UPPER(street_name) LIKE ?)')
        params += [f'{direction} %', f'% {direction}']

    for word in street_words:
        if len(word) == 1:
            # Single letter: match at start of name or after a space (any word start)
            conditions.append('(LOWER(street_name) LIKE ? OR LOWER(street_name) LIKE ?)')
            params += [f'{word}%', f'% {word}%']
        else:
            conditions.append('LOWER(street_name) LIKE ?')
            params.append(f'%{word}%')

    where = ' AND '.join(conditions) if conditions else '1=1'
    sql = f'''
        SELECT zip_code, street_name, range_start, range_end, even_odd, carrier
        FROM routes
        WHERE {where}
        ORDER BY street_name, range_start
        LIMIT 30
    '''

    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search_route():
    q = request.args.get('q', '')
    return jsonify(search(q))

@app.route('/carrier')
def carrier_route():
    q = request.args.get('q', '').strip().upper()
    if not re.match(r'^[CR]\d+$', q):
        return jsonify([])

    prefix = q[0]          # C or R
    digits = q[1:]          # the number portion typed

    # C%08%  → matches C080, C083, C086 …
    # C%86%  → matches C086
    # C%087% → matches C087
    pattern = f'{prefix}%{digits}%'

    conn = get_db()
    rows = conn.execute('''
        SELECT zip_code, street_name, range_start, range_end, even_odd, carrier
        FROM routes
        WHERE UPPER(carrier) LIKE ?
        ORDER BY street_name, range_start
    ''', (pattern,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
