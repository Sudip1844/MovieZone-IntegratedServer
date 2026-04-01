# IntegratedServer/database/supabase_client.py
# Python Supabase REST API client (ported from Movieweb/server/supabase-client.ts)

import os
import logging
import requests
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')


class SupabaseClient:
    """Supabase REST API client for database operations"""

    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            logger.warning('⚠️ Supabase not configured - some features may not work')
            self.base_url = ''
            self.headers = {}
            self.configured = False
            return

        self.base_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        self.configured = True
        logger.info('✅ Supabase REST client initialized')

    def select(self, table: str, columns: str = '*', where: Optional[Dict] = None,
               order: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Select rows from a table"""
        if not self.configured:
            return []
        try:
            url = f"{self.base_url}/{table}?select={columns}"
            if where:
                for key, value in where.items():
                    if isinstance(value, str) and value.startswith(('eq.', 'neq.', 'gt.', 'lt.', 'gte.', 'lte.', 'like.', 'ilike.')):
                        url += f"&{key}={value}"
                    else:
                        url += f"&{key}=eq.{value}"
            if order:
                url += f"&order={order}"
            if limit:
                url += f"&limit={limit}"

            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Supabase select error ({table}): {e}")
            return []

    def insert(self, table: str, data: Dict) -> Optional[Dict]:
        """Insert a row into a table"""
        if not self.configured:
            raise ConnectionError('Supabase not configured')
        try:
            resp = requests.post(
                f"{self.base_url}/{table}",
                headers=self.headers,
                json=data,
                timeout=15
            )
            resp.raise_for_status()
            result = resp.json()
            return result[0] if isinstance(result, list) and result else result
        except Exception as e:
            logger.error(f"Supabase insert error ({table}): {e}")
            raise

    def update(self, table: str, data: Dict, where: Dict) -> Optional[Dict]:
        """Update rows in a table"""
        if not self.configured:
            raise ConnectionError('Supabase not configured')
        try:
            conditions = "&".join(f"{k}=eq.{v}" for k, v in where.items())
            resp = requests.patch(
                f"{self.base_url}/{table}?{conditions}",
                headers=self.headers,
                json=data,
                timeout=15
            )
            resp.raise_for_status()
            result = resp.json()
            return result[0] if isinstance(result, list) and result else result
        except Exception as e:
            logger.error(f"Supabase update error ({table}): {e}")
            raise

    def delete(self, table: str, where: Dict) -> bool:
        """Delete rows from a table"""
        if not self.configured:
            raise ConnectionError('Supabase not configured')
        try:
            conditions = "&".join(f"{k}=eq.{v}" for k, v in where.items())
            resp = requests.delete(
                f"{self.base_url}/{table}?{conditions}",
                headers=self.headers,
                timeout=15
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Supabase delete error ({table}): {e}")
            raise

    def rpc(self, function_name: str, params: Optional[Dict] = None) -> Any:
        """Call a Supabase RPC function"""
        if not self.configured:
            raise ConnectionError('Supabase not configured')
        try:
            resp = requests.post(
                f"{self.base_url}/rpc/{function_name}",
                headers=self.headers,
                json=params or {},
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Supabase RPC error ({function_name}): {e}")
            raise

    def execute_sql(self, sql: str) -> Any:
        """Execute raw SQL via Supabase (uses direct PostgreSQL connection)"""
        import psycopg2
        db_host = os.getenv('SUPABASE_DB_HOST', '')
        db_name = os.getenv('SUPABASE_DB_NAME', 'postgres')
        db_user = os.getenv('SUPABASE_DB_USER', 'postgres')
        db_pass = os.getenv('SUPABASE_DB_PASSWORD', '')
        db_port = int(os.getenv('SUPABASE_DB_PORT', 5432))

        conn = psycopg2.connect(
            host=db_host, database=db_name, user=db_user,
            password=db_pass, port=db_port
        )
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                try:
                    return cur.fetchall()
                except Exception:
                    return None
        finally:
            conn.close()

    def test_connection(self) -> bool:
        """Test Supabase connection"""
        if not self.configured:
            logger.warning('⚠️ Supabase not configured - connection test skipped')
            return False
        try:
            resp = requests.get(
                f"{self.base_url}/movies?limit=1",
                headers=self.headers,
                timeout=10
            )
            logger.info('✅ Supabase REST API connection successful')
            return resp.ok
        except Exception as e:
            logger.error(f'❌ Supabase connection test failed: {e}')
            return False


# Global instance
supabase = SupabaseClient()
