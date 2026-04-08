from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker
from sqlalchemy import Text, String, Integer
import asyncio

engine = create_async_engine(url='sqlite+aiosqlite:///conspects.db')

async_session = async_sessionmaker(engine)

class BasicClass(AsyncAttrs, DeclarativeBase):
    pass

class Conspect(BasicClass):
    __tablename__ = 'conspects'
    id: Mapped[int] = mapped_column(primary_key=True)
    tags: Mapped[str] = mapped_column(String(250), nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    file_id: Mapped[str] = mapped_column(String(130), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(25), nullable=False)

async def init_db():
     async with engine.begin() as conn:
        await conn.run_sync(BasicClass.metadata.create_all)
       
if __name__ == "__main__":
    asyncio.run(init_db())


