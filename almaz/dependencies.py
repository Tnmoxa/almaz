import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

load_dotenv()

from openai import OpenAI
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


class SyncDatabase:

    def __init__(self, link: str):
        self.engine = create_engine(link)
        self._session_factory = sessionmaker(bind=self.engine)

    @contextmanager
    def __call__(self):
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()


class Database:

    def __init__(self, link):
        self.async_engine = create_async_engine(link)
        self._async_session = async_sessionmaker(self.async_engine, expire_on_commit=False)

    async def __call__(self):
        async with self._async_session() as session:
            yield session


class OpenAIApi:

    def __init__(self, api_key):
        if os.environ.get("SOCKS5_URL"):
            self.client = OpenAI(
                api_key=api_key,
                http_client=httpx.Client(proxy=os.environ.get("SOCKS5_URL"))
            )
        else:
            self.client = OpenAI(
                api_key=api_key,
            )
        self.openai_api_chat = self.client.chat.completions


logger = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S'))

file_handler = logging.FileHandler('logs/app.log', mode='a')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S'))

logger.addHandler(console_handler)
logger.addHandler(file_handler)

logger.setLevel(logging.INFO)

database = Database(os.environ.get('DATABASE_URL'))
sync_database = SyncDatabase(os.getenv("DATABASE_URL").replace('+asyncpg', ''))
openai_api = OpenAIApi(os.environ.get("OPENAI_API_KEY"))


@asynccontextmanager
async def lifespan(_):
    yield
