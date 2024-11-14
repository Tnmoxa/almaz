import logging
import os
import subprocess
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
    """
        Синхронный класс для работы с базой данных с использованием SQLAlchemy.

        Этот класс позволяет создавать синхронные соединения с базой данных и управлять сессиями.
        Он использует `create_engine` для создания подключения и `sessionmaker` для создания фабрики сессий.

        Attributes:
            engine: Экземпляр SQLAlchemy Engine для подключения к базе данных.
            _session_factory: Фабрика для создания сессий с базой данных.

        Methods:
            __call__: Создает и управляет сессией базы данных в рамках контекстного менеджера.

        Args:
            link (str): Строка подключения к базе данных.
        """

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
    """
       Асинхронный класс для работы с базой данных с использованием SQLAlchemy.

       Этот класс создает асинхронное соединение с базой данных и позволяет работать с асинхронными сессиями.
       Он использует `create_async_engine` для создания асинхронного подключения и `async_sessionmaker` для фабрики асинхронных сессий.

       Attributes:
           async_engine: Асинхронный SQLAlchemy Engine для подключения к базе данных.
           _async_session: Фабрика асинхронных сессий для взаимодействия с базой данных.

       Methods:
           __call__: Создает и управляет асинхронной сессией базы данных в рамках контекстного менеджера.

       Args:
           link (str): Строка подключения к базе данных.
       """

    def __init__(self, link):
        self.async_engine = create_async_engine(link)
        self._async_session = async_sessionmaker(self.async_engine, expire_on_commit=False)

    async def __call__(self):
        async with self._async_session() as session:
            yield session


class OpenAIApi:
    """
       Класс для взаимодействия с API OpenAI с использованием HTTP клиента.

       Этот класс предоставляет интерфейс для подключения к API OpenAI с возможностью проксирования через SOCKS5,
       если соответствующая переменная окружения задана. В противном случае API подключается напрямую.

       Attributes:
           client: Экземпляр клиента OpenAI для общения с API.
           openai_api_chat: Интерфейс для работы с чат-комплектациями OpenAI.

       Methods:
           __init__: Инициализация клиента OpenAI с заданным API-ключом.

       Args:
           api_key (str): API-ключ для подключения к OpenAI.
       """

    def __init__(self, api_key):
        if os.environ.get("SOCKS5_URL") and os.environ.get("OPENAI_API_KEY"):
            self.client = OpenAI(
                api_key=api_key,
                http_client=httpx.Client(proxy=os.environ.get("SOCKS5_URL"))
            )
            self.openai_api_chat = self.client.chat.completions
        elif os.environ.get("OPENAI_API_KEY"):
            self.client = OpenAI(
                api_key=api_key,
            )
            self.openai_api_chat = self.client.chat.completions
        else:
            self.openai_api_chat = None


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
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    yield
