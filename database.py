import re
from sqlalchemy import select, delete, or_, func
from models import Conspect, async_session

MAXIMUM_CONSPECTS = 85

class ConspectDataBase:
    
    @staticmethod
    async def generate_tegs(content):
        words = content.split()[:3]
        capitalized = re.findall(r'\b[А-ЯA-Z][а-яa-z]+\b', content)
        tags = list(set(words + capitalized))[:2]
        return ', '.join(tags) if tags else "нет тегов"

    @staticmethod
    async def save_conspect(user_id, content, content_type, file_id=None, tags=None):
            if tags is None:
               tags = await ConspectDataBase.generate_tegs(content)

            async with async_session() as session:
                async with session.begin():
                    conspect = Conspect(
                        user_id=user_id,
                        content=content,
                        content_type=content_type,
                        file_id=file_id,
                        tags=tags
                    )
                    session.add(conspect)
                return tags

    @staticmethod
    async def get_user_conspects(user_id):
        async with async_session() as session:
            stmt = select(Conspect).where(
                Conspect.user_id == user_id
            )

            result = await session.execute(stmt)
            conspects = result.scalars().all()

            conspects_list = []
            for conspect in conspects:
                conspect_data = (
                    conspect.id,
                    conspect.content,
                    conspect.content_type,
                    conspect.file_id,
                    conspect.tags,
                )
                conspects_list.append(conspect_data)
        return conspects_list
     
    @staticmethod
    async def delete_conspect(user_id, conspect_id):
        async with async_session() as session:  
            async with session.begin():
                stmt = delete(Conspect).where(
                    Conspect.id == conspect_id,
                    Conspect.user_id == user_id
                )
                result = await session.execute(stmt)
                return result.rowcount  
        
    @staticmethod
    async def delete_all_conspects(user_id):
        async with async_session() as session:  
            async with session.begin():
                stmt = delete(Conspect).where(
                    Conspect.user_id == user_id
                )
                result = await session.execute(stmt)   
                return result.rowcount  
    
    @staticmethod
    async def search_conspects(user_id, search_term):
     async with async_session() as session:
        search_pattern = f"%{search_term.lower()}%"
        
        stmt = (
            select(
                Conspect.id, 
                Conspect.content, 
                Conspect.content_type, 
                Conspect.file_id, 
                Conspect.tags
            )
            .where(Conspect.user_id == user_id)
            .where(
                or_(
                    Conspect.content.ilike(search_pattern),
                    Conspect.tags.ilike(search_pattern)
                )
            )
        )
        
        result = await session.execute(stmt)
        return result.all()
     
    @staticmethod
    async def get_count_by_user(user_id: int) -> int:
        async with async_session() as session:  
            query = select(func.count()).where(Conspect.user_id == user_id)
            result = await session.execute(query)
            return result.scalar() or 0
    
    @staticmethod
    async def is_limit_reached(user_id: int) -> bool:
      count = await ConspectDataBase.get_count_by_user(user_id)
      return count >= MAXIMUM_CONSPECTS