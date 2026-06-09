from flask import Blueprint, request, jsonify
from models.database import (
    add_catch_record, get_all_catches, get_catch_by_id, update_catch_record,
    delete_catch_record, like_catch_record
)
from collections import defaultdict

catches_bp = Blueprint('catches', __name__, url_prefix='/api/catches')

@catches_bp.route('', methods=['POST'])
def create_catch():
    """조과 기록 생성"""
    try:
        data = request.get_json()

        catch_id = add_catch_record(
            species=data.get('species', ''),
            size_cm=data.get('size_cm'),
            weight_g=data.get('weight_g'),
            spot_id=data.get('spot_id'),
            spot_name=data.get('spot_name', ''),
            location_lat=data.get('location_lat'),
            location_lng=data.get('location_lng'),
            gps_accuracy=data.get('gps_accuracy'),
            rod=data.get('rod', ''),
            reel=data.get('reel', ''),
            line_weight=data.get('line_weight', ''),
            leader=data.get('leader', ''),
            rig_method=data.get('rig_method', ''),
            caught_at=data.get('caught_at'),
            weather_condition=data.get('weather_condition', ''),
            tide_info=data.get('tide_info', ''),
            water_temp=data.get('water_temp'),
            depth_m=data.get('depth_m'),
            wind_speed=data.get('wind_speed'),
            hit_time=data.get('hit_time'),
            tidal_current=data.get('tidal_current'),
            tide_number=data.get('tide_number'),
            water_level=data.get('water_level'),
            user_nickname=data.get('user_nickname'),
            description=data.get('description', ''),
            photos=data.get('photos', ''),
            is_public=data.get('is_public', False),
            user_id=data.get('user_id')
        )

        return jsonify({'id': catch_id, 'message': '조과 기록이 저장되었습니다'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('', methods=['GET'])
def fetch_catches():
    """조과 기록 조회"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        sort = request.args.get('sort', 'latest', type=str)

        catches = get_all_catches(limit=limit, offset=offset, sort_by=sort)

        return jsonify(catches), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/<int:catch_id>', methods=['GET'])
def fetch_catch(catch_id):
    """조과 기록 상세 조회"""
    try:
        catch = get_catch_by_id(catch_id)

        if not catch:
            return jsonify({'error': '조과 기록을 찾을 수 없습니다'}), 404

        return jsonify(catch), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/<int:catch_id>', methods=['PUT'])
def update_catch(catch_id):
    """조과 기록 수정"""
    try:
        data = request.get_json()

        success = update_catch_record(catch_id, **data)

        if not success:
            return jsonify({'error': '업데이트할 데이터가 없습니다'}), 400

        return jsonify({'message': '조과 기록이 수정되었습니다'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/<int:catch_id>', methods=['DELETE'])
def delete_catch(catch_id):
    """조과 기록 삭제"""
    try:
        delete_catch_record(catch_id)

        return jsonify({'message': '조과 기록이 삭제되었습니다'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/<int:catch_id>/like', methods=['POST'])
def add_like(catch_id):
    """조과 기록 좋아요"""
    try:
        like_catch_record(catch_id)

        return jsonify({'message': '좋아요를 추가했습니다'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/feed', methods=['GET'])
def fetch_feed():
    """SNS 피드 조회"""
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        sort = request.args.get('sort', 'latest', type=str)
        species = request.args.get('species', None, type=str)

        catches = get_all_catches(limit=limit, offset=offset, sort_by=sort)

        # 어종 필터링
        if species:
            catches = [c for c in catches if c.get('species') == species]

        return jsonify(catches), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/generate-test', methods=['POST'])
def generate_test_data():
    """테스트 데이터 생성 - 인천 50개 + 군산 50개"""
    try:
        import random
        from datetime import datetime, timedelta

        # 지역별 설정
        incheon_species = ['우럭', '광어', '농어', '전갈이']
        incheon_spots = ['인천 영종대교', '인천 월미도', '인천 팔미도', '인천 선재도', '인천 무의도']
        incheon_coords = [(37.35, 126.63), (37.27, 126.58), (37.40, 126.70), (37.32, 126.65), (37.38, 126.57)]

        gunsan_species = ['우럭', '광어', '감성돔', '방어']
        gunsan_spots = ['군산 야미도', '군산 비응도', '군산 선유도', '군산 고군산군도', '군산 어청도']
        gunsan_coords = [(35.98, 126.62), (36.01, 126.68), (36.03, 126.65), (35.99, 126.72), (36.05, 126.55)]

        rods = ['샤마 6ft', '아부 4ft', '시마노 5ft', '다이와 6ft', '델타 7ft']
        reels = ['시마노 3000', '다이와 2500', '시마노 4000', '다이와 3000', '아부가르시아 3500']
        line_weights = ['PE 1.0호', 'PE 1.5호', 'PE 2.0호']
        leaders = ['나일론 2호', '나일론 3호', '나일론 4호']
        rig_methods = ['벵디그로', '스핀', '이싱', '볼헤드', '지그헤드']
        nicknames = ['낚시꾼', '바다사나이', '물때마스터', '조류사냥꾼', '파도여사', '손맛좋은아저씨', '대물사냥꾼']

        created_count = 0

        # 인천 50개 생성
        for _ in range(50):
            days_ago = random.randint(0, 30)
            caught_date = datetime.now() - timedelta(days=days_ago)
            caught_date = caught_date.replace(hour=random.randint(6, 18), minute=random.randint(0, 59))

            species = random.choice(incheon_species)
            size_cm = round(random.uniform(28, 50), 1)
            spot_idx = random.randint(0, len(incheon_spots) - 1)
            spot_name = incheon_spots[spot_idx]
            lat, lng = incheon_coords[spot_idx]
            location_lat = lat + random.uniform(-0.01, 0.01)
            location_lng = lng + random.uniform(-0.01, 0.01)

            catch_id = add_catch_record(
                species=species,
                size_cm=size_cm,
                spot_name=spot_name,
                location_lat=location_lat,
                location_lng=location_lng,
                rod=random.choice(rods),
                reel=random.choice(reels),
                line_weight=random.choice(line_weights),
                leader=random.choice(leaders),
                rig_method=random.choice(rig_methods),
                user_nickname=random.choice(nicknames),
                tide_number=random.randint(1, 15),
                water_level=round(random.uniform(1.0, 3.5), 2),
                tidal_current=round(random.uniform(0.2, 1.0), 2),
                wind_speed=round(random.uniform(1.0, 8.0), 1),
                description=f'{spot_name}에서 {species} {size_cm}cm 낚시 성공!',
                is_public=True,
                user_id=random.randint(1, 5),
                caught_at=caught_date.isoformat()
            )
            if catch_id:
                created_count += 1

        # 군산 50개 생성
        for _ in range(50):
            days_ago = random.randint(0, 30)
            caught_date = datetime.now() - timedelta(days=days_ago)
            caught_date = caught_date.replace(hour=random.randint(6, 18), minute=random.randint(0, 59))

            species = random.choice(gunsan_species)
            size_cm = round(random.uniform(30, 55), 1)
            spot_idx = random.randint(0, len(gunsan_spots) - 1)
            spot_name = gunsan_spots[spot_idx]
            lat, lng = gunsan_coords[spot_idx]
            location_lat = lat + random.uniform(-0.01, 0.01)
            location_lng = lng + random.uniform(-0.01, 0.01)

            catch_id = add_catch_record(
                species=species,
                size_cm=size_cm,
                spot_name=spot_name,
                location_lat=location_lat,
                location_lng=location_lng,
                rod=random.choice(rods),
                reel=random.choice(reels),
                line_weight=random.choice(line_weights),
                leader=random.choice(leaders),
                rig_method=random.choice(rig_methods),
                user_nickname=random.choice(nicknames),
                tide_number=random.randint(1, 15),
                water_level=round(random.uniform(1.0, 3.5), 2),
                tidal_current=round(random.uniform(0.2, 1.0), 2),
                wind_speed=round(random.uniform(1.0, 8.0), 1),
                description=f'{spot_name}에서 {species} {size_cm}cm 낚시 성공!',
                is_public=True,
                user_id=random.randint(1, 5),
                caught_at=caught_date.isoformat()
            )
            if catch_id:
                created_count += 1

        return jsonify({'message': f'{created_count}개의 테스트 데이터 생성 완료 (인천: 50개, 군산: 50개)'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/nearby', methods=['GET'])
def fetch_nearby_catches():
    """주변 위치의 조과 기록 조회 (거리, 날짜, 어종 기반)"""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        distance_km = request.args.get('distance', 10, type=float)
        sort = request.args.get('sort', 'latest', type=str)
        date_filter = request.args.get('date', type=str)  # YYYY-MM-DD
        species_filter = request.args.get('species', type=str)

        if lat is None or lng is None:
            return jsonify({'error': '위도와 경도가 필요합니다'}), 400

        # 모든 공개 기록 조회
        catches = get_all_catches(limit=1000)
        public_catches = [c for c in catches if c.get('is_public')]

        # Haversine 공식으로 거리 계산
        import math
        from datetime import datetime

        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371  # 지구 반지름 (km)
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return R * c

        # 필터링 및 거리 계산
        nearby = []
        for catch in public_catches:
            if not catch.get('location_lat') or not catch.get('location_lng'):
                continue

            dist = haversine_distance(lat, lng, catch['location_lat'], catch['location_lng'])
            if dist > distance_km:
                continue

            # 날짜 필터 (시작 날짜가 같은 날짜인지 확인)
            if date_filter:
                try:
                    caught_at = datetime.fromisoformat(catch['caught_at'].replace('Z', '+00:00'))
                    if caught_at.strftime('%Y-%m-%d') != date_filter:
                        continue
                except:
                    pass

            # 어종 필터
            if species_filter:
                if not catch.get('species') or species_filter not in catch['species']:
                    continue

            catch['distance_km'] = round(dist, 2)
            nearby.append(catch)

        # 소팅
        if sort == 'views':
            nearby.sort(key=lambda x: x.get('view_count', 0), reverse=True)
        elif sort == 'species':
            nearby.sort(key=lambda x: x.get('species', ''))
        else:  # latest or distance (거리순)
            nearby.sort(key=lambda x: x.get('distance_km', 0))

        return jsonify(nearby), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# 등급 계산 함수
def calculate_score(total_catches, max_size, average_size, likes):
    return int((total_catches * 10) + (max_size * 2) + (average_size * 5) + (likes * 5))

def get_grade(score):
    if score < 51:
        return {'emoji': '🎣', 'name': '막내 낚시꾼', 'desc': '이제 시작이에요!'}
    elif score < 151:
        return {'emoji': '🌊', 'name': '물때 배우는중', 'desc': '물때 감을 익혀요!'}
    elif score < 301:
        return {'emoji': '🎯', 'name': '묵직한 손맛', 'desc': '조황을 알아요!'}
    elif score < 501:
        return {'emoji': '👑', 'name': '대물사냥꾼', 'desc': '큰 고기가 나를 부릅니다!'}
    elif score < 801:
        return {'emoji': '🏆', 'name': '낚시의 신', 'desc': '바다가 나를 따라요!'}
    else:
        return {'emoji': '👨‍⚓', 'name': '영광의 어사', 'desc': '낚시의 전설입니다!'}

@catches_bp.route('/rankings/grade', methods=['GET'])
def get_grade_rankings():
    """등급 랭킹 (상위 10명)"""
    try:
        catches = get_all_catches(limit=1000)
        public_catches = [c for c in catches if c.get('is_public')]

        # 사용자별 통계 계산
        user_stats = defaultdict(lambda: {'total': 0, 'max_size': 0, 'sizes': [], 'likes': 0})

        for catch in public_catches:
            user_id = catch.get('user_id') or catch.get('user_nickname') or '익명'
            user_stats[user_id]['total'] += 1
            user_stats[user_id]['max_size'] = max(user_stats[user_id]['max_size'], catch.get('size_cm', 0))
            user_stats[user_id]['sizes'].append(catch.get('size_cm', 0))
            user_stats[user_id]['likes'] += catch.get('like_count', 0)

        # 점수 계산
        rankings = []
        for user_id, stats in user_stats.items():
            avg_size = sum(stats['sizes']) / len(stats['sizes']) if stats['sizes'] else 0
            score = calculate_score(stats['total'], stats['max_size'], avg_size, stats['likes'])
            grade = get_grade(score)

            rankings.append({
                'userId': user_id,
                'score': score,
                'grade': f"{grade['emoji']} {grade['name']}",
                'gradeDesc': grade['desc']
            })

        # 점수순 정렬 (내림차순)
        rankings.sort(key=lambda x: x['score'], reverse=True)

        return jsonify(rankings[:10]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/rankings/max-size', methods=['GET'])
def get_max_size_rankings():
    """최대어 랭킹 (상위 10명)"""
    try:
        catches = get_all_catches(limit=1000)
        public_catches = [c for c in catches if c.get('is_public')]

        # 사용자별 최대어 찾기
        max_fish = {}
        for catch in public_catches:
            user_id = catch.get('user_id') or catch.get('user_nickname') or '익명'

            if user_id not in max_fish or catch.get('size_cm', 0) > max_fish[user_id].get('size', 0):
                max_fish[user_id] = {
                    'userId': user_id,
                    'species': catch.get('species', '-'),
                    'size': catch.get('size_cm', 0)
                }

        # 크기순 정렬
        rankings = sorted(max_fish.values(), key=lambda x: x['size'], reverse=True)

        return jsonify(rankings[:10]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/rankings/count', methods=['GET'])
def get_count_rankings():
    """다작 랭킹 - 마리수 기준 (상위 10명)"""
    try:
        catches = get_all_catches(limit=1000)
        public_catches = [c for c in catches if c.get('is_public')]

        # 사용자별 마리수 계산
        count_by_user = defaultdict(int)
        for catch in public_catches:
            user_id = catch.get('user_id') or catch.get('user_nickname') or '익명'
            count_by_user[user_id] += 1

        # 마리수순 정렬
        rankings = [{'userId': user_id, 'count': count} for user_id, count in count_by_user.items()]
        rankings.sort(key=lambda x: x['count'], reverse=True)

        return jsonify(rankings[:10]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
