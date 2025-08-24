#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('/app')

from app.infrastructure.database.session import get_db_context
from sqlalchemy import text

async def check_users():
    async with get_db_context() as session:
        result = await session.execute(text('SELECT email, password_hash FROM users LIMIT 5'))
        users = result.fetchall()
        print('Users in database:')
        for user in users:
            print(f'Email: {user[0]}, Hash: {user[1][:50] if user[1] else "None"}...')

if __name__ == '__main__':
    asyncio.run(check_users())