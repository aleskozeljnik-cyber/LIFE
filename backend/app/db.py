from psycopg import AsyncConnection
from psycopg.rows import dict_row
from .config import settings

async def get_connection():
    return await AsyncConnection.connect(settings.database_url, row_factory=dict_row)
