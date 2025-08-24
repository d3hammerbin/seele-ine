#!/usr/bin/env python3

import asyncio
import uuid
from datetime import datetime
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.database.session import get_session_manager
from app.infrastructure.database.models.user import UserModel
from app.core.security.jwt_service import jwt_service
from sqlalchemy import text
from datetime import datetime

async def create_test_user():
    # Initialize database manager
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # Get session manager
    session_manager = get_session_manager()
    session = session_manager.get_session()
    
    try:
        # Check if test user already exists
        result = await session.execute(
            text('SELECT id FROM users WHERE email = :email'),
            {'email': 'test@example.com'}
        )
        existing_user = result.fetchone()
        
        if existing_user:
            print('Test user already exists, updating password...')
            hashed_password = jwt_service.hash_password('testpassword123')
            await session.execute(
                text('UPDATE users SET password_hash = :password WHERE email = :email'),
                {'password': hashed_password, 'email': 'test@example.com'}
            )
        else:
            print('Creating new test user...')
            hashed_password = jwt_service.hash_password('testpassword123')
            user_id = str(uuid.uuid4())
            
            await session.execute(
                text('''
                    INSERT INTO users (
                        id, email, username, password_hash, first_name, last_name,
                        role, status, subscription_plan, is_email_verified, preferences,
                        stats, created_at, updated_at
                    ) VALUES (
                        :id, :email, :username, :password_hash, :first_name, :last_name,
                        :role, :status, :subscription_plan, :is_email_verified, :preferences,
                        :stats, :created_at, :updated_at
                    )
                '''),
                {
                    'id': user_id,
                    'email': 'test@example.com',
                    'username': 'testuser',
                    'password_hash': hashed_password,
                    'first_name': 'Test',
                    'last_name': 'User',
                    'role': 'user',
                    'status': 'active',
                    'subscription_plan': 'basic',
                    'is_email_verified': True,
                    'preferences': '{}',
                    'stats': '{}',
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
            )
        
        await session.commit()
        print('✅ Test user created/updated successfully!')
        
    except Exception as e:
        await session.rollback()
        print(f'❌ Error: {e}')
        raise
    finally:
        await session.close()
        await db_manager.close()

if __name__ == '__main__':
    asyncio.run(create_test_user())