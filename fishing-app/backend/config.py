import os
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


class Config:
    """애플리케이션 설정 관리 (secret.toml + 환경변수)"""

    def __init__(self):
        self.config_path = Path(__file__).parent / 'secret.toml'
        self._load_config()

    def _load_config(self):
        """secret.toml 파일 로드 및 환경변수 병합"""
        config_data = {}

        # 1. secret.toml 읽기
        if self.config_path.exists():
            try:
                with open(self.config_path, 'rb') as f:
                    config_data = tomllib.load(f)
            except Exception as e:
                print(f"경고: secret.toml 읽기 실패 - {e}")
        else:
            print(f"경고: secret.toml 파일을 찾을 수 없습니다: {self.config_path}")

        # 2. TOML 데이터 저장
        self.api_config = config_data.get('api', {})
        self.app_config = config_data.get('app', {})

        # 3. 환경변수로 오버라이드 (환경변수가 우선)
        self.api_config['kma_service_key'] = os.getenv(
            'KMA_SERVICE_KEY',
            self.api_config.get('kma_service_key')
        )
        self.api_config['khoa_service_key'] = os.getenv(
            'KHOA_SERVICE_KEY',
            self.api_config.get('khoa_service_key')
        )
        self.api_config['fishing_index_api_key'] = os.getenv(
            'FISHING_INDEX_API_KEY',
            self.api_config.get('fishing_index_api_key')
        )

        self.app_config['environment'] = os.getenv(
            'FLASK_ENV',
            self.app_config.get('environment', 'development')
        )
        self.app_config['debug'] = os.getenv(
            'FLASK_DEBUG',
            str(self.app_config.get('debug', False))
        ).lower() in ('true', '1', 'yes')

    def get_api_key(self, key_name: str, required: bool = False) -> str:
        """API 키 조회 및 검증

        Args:
            key_name: 'kma_service_key', 'khoa_service_key', 'fishing_index_api_key'
            required: 필수 여부

        Returns:
            API 키 값

        Raises:
            ValueError: 필수 키가 없을 때
        """
        value = self.api_config.get(key_name, '')

        if required and (not value or value.startswith('dummy_') or value.startswith('your_')):
            raise ValueError(
                f"필수 API 키가 설정되지 않았습니다: {key_name}\n"
                f"secret.toml 파일을 생성하고 API 키를 입력하세요.\n"
                f"참조: secret.toml.example"
            )

        return value

    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.app_config.get('environment') == 'production'


# 전역 설정 인스턴스
config = Config()
