import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'fishing_app.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fishing_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            description TEXT,
            fish_types TEXT,
            photo_url TEXT,
            reel TEXT,
            rod TEXT,
            tackle TEXT,
            rig_memo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    try:
        cursor.execute('ALTER TABLE fishing_points ADD COLUMN photo_url TEXT')
        cursor.execute('ALTER TABLE fishing_points ADD COLUMN reel TEXT')
        cursor.execute('ALTER TABLE fishing_points ADD COLUMN rod TEXT')
        cursor.execute('ALTER TABLE fishing_points ADD COLUMN tackle TEXT')
        cursor.execute('ALTER TABLE fishing_points ADD COLUMN rig_memo TEXT')
    except:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS known_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            region TEXT,
            fish_types TEXT,
            description TEXT
        )
    ''')

    cursor.execute('SELECT COUNT(*) FROM known_spots')
    if cursor.fetchone()[0] == 0:
        seed_known_spots()

    # 조과 기록 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS catch_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            species TEXT NOT NULL,
            size_cm REAL,
            weight_g REAL,
            spot_id INTEGER,
            spot_name TEXT,
            location_lat REAL,
            location_lng REAL,
            gps_accuracy INTEGER,
            rod TEXT,
            reel TEXT,
            line_weight TEXT,
            leader TEXT,
            rig_method TEXT,
            caught_at TIMESTAMP NOT NULL,
            weather_condition TEXT,
            tide_info TEXT,
            water_temp REAL,
            description TEXT,
            photos TEXT,
            is_public BOOLEAN DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 좋아요 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS catch_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            catch_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(catch_id) REFERENCES catch_records(id) ON DELETE CASCADE
        )
    ''')

    # 방문 이력 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fishing_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_id INTEGER,
            spot_name TEXT,
            visited_at TIMESTAMP NOT NULL,
            duration_minutes INTEGER,
            catch_count INTEGER,
            weather TEXT,
            tide_info TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 즐겨찾기 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorite_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_id INTEGER,
            spot_name TEXT,
            spot_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def add_fishing_point(name, latitude, longitude, description='', fish_types='', photo_url='', reel='', rod='', tackle='', rig_memo=''):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO fishing_points (name, latitude, longitude, description, fish_types, photo_url, reel, rod, tackle, rig_memo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, latitude, longitude, description, fish_types, photo_url, reel, rod, tackle, rig_memo))

    conn.commit()
    point_id = cursor.lastrowid
    conn.close()

    return point_id

def get_all_points():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM fishing_points ORDER BY created_at DESC')
    points = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return points

def get_point_by_id(point_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM fishing_points WHERE id = ?', (point_id,))
    row = cursor.fetchone()

    conn.close()
    return dict(row) if row else None

def delete_point(point_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM fishing_points WHERE id = ?', (point_id,))
    conn.commit()
    conn.close()

def update_point(point_id, **kwargs):
    conn = get_connection()
    cursor = conn.cursor()

    allowed_fields = {'name', 'description', 'fish_types', 'photo_url', 'reel', 'rod', 'tackle', 'rig_memo'}
    update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not update_fields:
        conn.close()
        return False

    set_clause = ', '.join(f'{k} = ?' for k in update_fields.keys())
    values = list(update_fields.values()) + [point_id]

    cursor.execute(f'UPDATE fishing_points SET {set_clause} WHERE id = ?', values)
    conn.commit()
    conn.close()

    return True

KNOWN_SPOTS_SEED = [
    ('인천 소래포구', 37.4337, 126.7355, '서해', '참조기,망둑어,숭어', '서해 대표 선상낚시 포인트'),
    ('태안 안면도', 36.4756, 126.3750, '서해', '우럭,광어,놀래미', '태안 갯바위 명소'),
    ('서천 장항', 36.2811, 126.6919, '서해', '숭어,우럭,농어', '장항 선상낚시 출발지'),
    ('군산 비응항', 35.9676, 126.5867, '서해', '광어,우럭,쥐치', '군산 선상낚시 명소'),
    ('목포 달리도', 34.8118, 126.2900, '남해', '감성돔,숭어,농어', '남해 갯바위 포인트'),
    ('여수 돌산도', 34.6897, 127.7041, '남해', '감성돔,볼락,문어', '여수 갯바위 명소'),
    ('통영 욕지도', 34.5892, 128.2250, '남해', '참돔,삼치,갈치', '통영 원도 낚시'),
    ('거제 학동', 34.8169, 128.6522, '남해', '감성돔,쥐치,볼락', '거제도 갯바위'),
    ('부산 기장', 35.2437, 129.2195, '동해', '우럭,문어,학꽁치', '기장 갯바위 포인트'),
    ('울산 강동', 35.6244, 129.4468, '동해', '감성돔,볼락,도루묵', '동해 갯바위'),
    ('포항 구룡포', 35.9882, 129.5566, '동해', '대구,방어,오징어', '동해안 선상낚시'),
    ('강릉 연곡', 37.8561, 128.9102, '동해', '연어,은어,송어', '동해 계류낚시'),
    ('제주 한림항', 33.4140, 126.2617, '제주', '갈치,고등어,자리돔', '제주 선상낚시'),
    ('서귀포 보목', 33.2495, 126.5833, '제주', '자바리,돔,방어', '제주 갯바위 명소'),
    ('제주 협재', 33.3945, 126.2329, '제주', '감성돔,볼락,우럭', '제주 갯바위 포인트'),
    ('인천 을왕리', 37.4234, 126.4356, '서해', '우럭,놀래미,쥐치', '을왕리 갯바위'),
    ('경주 문무대왕릉', 36.8951, 129.4329, '동해', '학꽁치,고등어,방어', '경주 해안 낚시'),
    ('남해 독일마을', 34.8730, 128.0678, '남해', '우럭,광어,농어', '남해 남동부 포인트'),
    ('통영 벽이도', 34.4267, 128.4532, '남해', '감성돔,방어,삼치', '통영 남쪽 갯바위'),
    ('거제 홍포', 34.8901, 128.7234, '남해', '감성돔,볼락,광어', '거제 동쪽 포인트'),
    ('포항 호미곶', 36.0789, 129.5678, '동해', '우럭,감성돔,문어', '호미곶 갯바위 명소'),
    ('강원 정동진', 37.3156, 129.1123, '동해', '은어,송어,도루묵', '정동진 계류'),
    ('속초 청초호', 38.1856, 128.5934, '동해', '송어,은어,잉어', '속초 계류 명소'),
    ('원주 남한강', 37.3364, 127.9789, '내수면', '연어,은어,쏘가리', '남한강 계류낚시'),
    ('여주 강변', 37.2764, 127.6356, '내수면', '붕어,잉어,쏘가리', '여주 잉어 명소'),
]

def seed_known_spots():
    conn = get_connection()
    cursor = conn.cursor()

    for name, lat, lng, region, fish_types, desc in KNOWN_SPOTS_SEED:
        cursor.execute('''
            INSERT INTO known_spots (name, latitude, longitude, region, fish_types, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, lat, lng, region, fish_types, desc))

    conn.commit()
    conn.close()

def get_all_spots(species=None):
    conn = get_connection()
    cursor = conn.cursor()

    if species:
        cursor.execute('''
            SELECT * FROM known_spots
            WHERE fish_types LIKE ?
            ORDER BY region, name
        ''', (f'%{species}%',))
    else:
        cursor.execute('SELECT * FROM known_spots ORDER BY region, name')

    spots = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return spots

def get_all_species():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT fish_types FROM known_spots')
    rows = cursor.fetchall()
    conn.close()

    species_set = set()
    for row in rows:
        if row[0]:
            species = row[0].split(',')
            for s in species:
                species_set.add(s.strip())

    return sorted(list(species_set))

# ===== 조과 기록 관련 함수 =====

def add_catch_record(species, size_cm=None, weight_g=None, spot_id=None, spot_name='',
                     location_lat=None, location_lng=None, gps_accuracy=None,
                     rod='', reel='', line_weight='', leader='', rig_method='',
                     caught_at=None, weather_condition='', tide_info='', water_temp=None,
                     description='', photos='', is_public=False, user_id=None):
    """조과 기록 추가"""
    conn = get_connection()
    cursor = conn.cursor()

    if caught_at is None:
        caught_at = datetime.now().isoformat()

    cursor.execute('''
        INSERT INTO catch_records
        (user_id, species, size_cm, weight_g, spot_id, spot_name, location_lat, location_lng, gps_accuracy,
         rod, reel, line_weight, leader, rig_method, caught_at, weather_condition, tide_info, water_temp,
         description, photos, is_public)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, species, size_cm, weight_g, spot_id, spot_name, location_lat, location_lng, gps_accuracy,
          rod, reel, line_weight, leader, rig_method, caught_at, weather_condition, tide_info, water_temp,
          description, photos, is_public))

    conn.commit()
    catch_id = cursor.lastrowid
    conn.close()

    return catch_id

def get_all_catches(limit=50, offset=0, sort_by='latest'):
    """모든 조과 기록 조회"""
    conn = get_connection()
    cursor = conn.cursor()

    if sort_by == 'views':
        cursor.execute('SELECT * FROM catch_records ORDER BY view_count DESC LIMIT ? OFFSET ?', (limit, offset))
    elif sort_by == 'likes':
        cursor.execute('SELECT * FROM catch_records ORDER BY like_count DESC LIMIT ? OFFSET ?', (limit, offset))
    else:  # latest
        cursor.execute('SELECT * FROM catch_records ORDER BY caught_at DESC LIMIT ? OFFSET ?', (limit, offset))

    catches = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return catches

def get_catch_by_id(catch_id):
    """특정 조과 기록 조회"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM catch_records WHERE id = ?', (catch_id,))
    row = cursor.fetchone()

    if row:
        row = dict(row)
        # view_count 증가
        cursor.execute('UPDATE catch_records SET view_count = view_count + 1 WHERE id = ?', (catch_id,))
        conn.commit()

    conn.close()
    return row

def update_catch_record(catch_id, **kwargs):
    """조과 기록 수정"""
    conn = get_connection()
    cursor = conn.cursor()

    allowed_fields = {'species', 'size_cm', 'weight_g', 'spot_id', 'spot_name', 'weather_condition', 'tide_info', 'water_temp', 'description', 'photos'}
    update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not update_fields:
        conn.close()
        return False

    set_clause = ', '.join(f'{k} = ?' for k in update_fields.keys())
    values = list(update_fields.values()) + [catch_id]

    cursor.execute(f'UPDATE catch_records SET {set_clause} WHERE id = ?', values)
    conn.commit()
    conn.close()

    return True

def delete_catch_record(catch_id):
    """조과 기록 삭제"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM catch_records WHERE id = ?', (catch_id,))
    conn.commit()
    conn.close()

def like_catch_record(catch_id):
    """조과 기록 좋아요"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO catch_likes (catch_id) VALUES (?)', (catch_id,))
    cursor.execute('UPDATE catch_records SET like_count = like_count + 1 WHERE id = ?', (catch_id,))

    conn.commit()
    conn.close()

# ===== 방문 이력 관련 함수 =====

def add_fishing_session(spot_id=None, spot_name='', visited_at=None, duration_minutes=None, catch_count=0, weather='', tide_info='', notes=''):
    """방문 이력 추가"""
    conn = get_connection()
    cursor = conn.cursor()

    if visited_at is None:
        visited_at = datetime.now().isoformat()

    cursor.execute('''
        INSERT INTO fishing_sessions
        (spot_id, spot_name, visited_at, duration_minutes, catch_count, weather, tide_info, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (spot_id, spot_name, visited_at, duration_minutes, catch_count, weather, tide_info, notes))

    conn.commit()
    session_id = cursor.lastrowid
    conn.close()

    return session_id

def get_fishing_history(limit=50, offset=0):
    """방문 이력 조회"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM fishing_sessions ORDER BY visited_at DESC LIMIT ? OFFSET ?', (limit, offset))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return history

# ===== 즐겨찾기 관련 함수 =====

def add_favorite_spot(spot_id, spot_name='', spot_type='known'):
    """즐겨찾기 추가"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO favorite_spots (spot_id, spot_name, spot_type) VALUES (?, ?, ?)', (spot_id, spot_name, spot_type))
    conn.commit()
    fav_id = cursor.lastrowid
    conn.close()

    return fav_id

def get_favorite_spots():
    """즐겨찾기 조회"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM favorite_spots ORDER BY created_at DESC')
    favorites = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return favorites

def remove_favorite_spot(favorite_id):
    """즐겨찾기 제거"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM favorite_spots WHERE id = ?', (favorite_id,))
    conn.commit()
    conn.close()

# ===== 통계 관련 함수 =====

def get_user_stats():
    """사용자 통계"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as total_catches FROM catch_records')
    total = cursor.fetchone()['total_catches'] or 0

    cursor.execute('SELECT AVG(size_cm) as avg_size FROM catch_records')
    avg_size = cursor.fetchone()['avg_size'] or 0

    cursor.execute('SELECT species, COUNT(*) as count FROM catch_records GROUP BY species ORDER BY count DESC LIMIT 1')
    favorite = cursor.fetchone()

    conn.close()

    return {
        'total_catches': total,
        'avg_size': avg_size,
        'favorite_species': favorite['species'] if favorite else None
    }
