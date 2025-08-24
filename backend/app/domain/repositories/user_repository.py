#!/usr/bin/env python3
"""
Repositorio de Usuario para SEELE-E Backend

Define la interfaz del repositorio para la entidad User,
siguiendo los principios de Clean Architecture.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from ..entities.user import User, UserRole, UserStatus, SubscriptionPlan


class UserRepository(ABC):
    """
    Interfaz del repositorio para la entidad User.
    
    Define los métodos que debe implementar cualquier repositorio
    concreto para el manejo de usuarios.
    """
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """
        Crea un nuevo usuario en el repositorio.
        
        Args:
            user: Entidad User a crear
            
        Returns:
            User: Usuario creado con ID asignado
            
        Raises:
            RepositoryError: Si ocurre un error en el repositorio
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Optional[User]: Usuario encontrado o None
        """
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Optional[User]: Usuario encontrado o None
        """
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Obtiene un usuario por su nombre de usuario.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Optional[User]: Usuario encontrado o None
        """
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """
        Actualiza un usuario existente.
        
        Args:
            user: Entidad User con los datos actualizados
            
        Returns:
            User: Usuario actualizado
            
        Raises:
            RepositoryError: Si el usuario no existe o hay error
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """
        Elimina un usuario del repositorio.
        
        Args:
            user_id: ID del usuario a eliminar
            
        Returns:
            bool: True si se eliminó correctamente
        """
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """
        Verifica si existe un usuario con el email dado.
        
        Args:
            email: Email a verificar
            
        Returns:
            bool: True si existe un usuario con ese email
        """
        pass
    
    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """
        Verifica si existe un usuario con el username dado.
        
        Args:
            username: Username a verificar
            
        Returns:
            bool: True si existe un usuario con ese username
        """
        pass
    
    @abstractmethod
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        subscription_plan: Optional[SubscriptionPlan] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> List[User]:
        """
        Lista usuarios con filtros y paginación.
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            role: Filtrar por rol
            status: Filtrar por estado
            subscription_plan: Filtrar por plan de suscripción
            search: Texto de búsqueda (nombre, email, username)
            sort_by: Campo por el cual ordenar
            sort_desc: Si ordenar descendente
            
        Returns:
            List[User]: Lista de usuarios
        """
        pass
    
    @abstractmethod
    async def count_users(
        self,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        subscription_plan: Optional[SubscriptionPlan] = None,
        search: Optional[str] = None
    ) -> int:
        """
        Cuenta el número total de usuarios con filtros.
        
        Args:
            role: Filtrar por rol
            status: Filtrar por estado
            subscription_plan: Filtrar por plan de suscripción
            search: Texto de búsqueda
            
        Returns:
            int: Número total de usuarios
        """
        pass
    
    @abstractmethod
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """
        Obtiene todos los usuarios con un rol específico.
        
        Args:
            role: Rol a filtrar
            
        Returns:
            List[User]: Lista de usuarios con el rol especificado
        """
        pass
    
    @abstractmethod
    async def get_users_by_status(self, status: UserStatus) -> List[User]:
        """
        Obtiene todos los usuarios con un estado específico.
        
        Args:
            status: Estado a filtrar
            
        Returns:
            List[User]: Lista de usuarios con el estado especificado
        """
        pass
    
    @abstractmethod
    async def get_users_by_subscription_plan(self, plan: SubscriptionPlan) -> List[User]:
        """
        Obtiene todos los usuarios con un plan de suscripción específico.
        
        Args:
            plan: Plan de suscripción a filtrar
            
        Returns:
            List[User]: Lista de usuarios con el plan especificado
        """
        pass
    
    @abstractmethod
    async def get_users_created_between(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[User]:
        """
        Obtiene usuarios creados entre dos fechas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            List[User]: Lista de usuarios creados en el rango
        """
        pass
    
    @abstractmethod
    async def get_users_last_login_before(self, date: datetime) -> List[User]:
        """
        Obtiene usuarios cuyo último login fue antes de la fecha dada.
        
        Args:
            date: Fecha límite
            
        Returns:
            List[User]: Lista de usuarios inactivos
        """
        pass
    
    @abstractmethod
    async def update_last_login(self, user_id: UUID, login_time: datetime) -> bool:
        """
        Actualiza la fecha de último login de un usuario.
        
        Args:
            user_id: ID del usuario
            login_time: Fecha y hora del login
            
        Returns:
            bool: True si se actualizó correctamente
        """
        pass
    
    @abstractmethod
    async def increment_login_count(self, user_id: UUID) -> bool:
        """
        Incrementa el contador de logins de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            bool: True si se actualizó correctamente
        """
        pass
    
    @abstractmethod
    async def update_user_stats(
        self, 
        user_id: UUID, 
        stats_update: Dict[str, Any]
    ) -> bool:
        """
        Actualiza las estadísticas de un usuario.
        
        Args:
            user_id: ID del usuario
            stats_update: Diccionario con las estadísticas a actualizar
            
        Returns:
            bool: True si se actualizó correctamente
        """
        pass
    
    @abstractmethod
    async def soft_delete(self, user_id: UUID) -> bool:
        """
        Realiza un borrado suave del usuario (marca como eliminado).
        
        Args:
            user_id: ID del usuario
            
        Returns:
            bool: True si se marcó como eliminado correctamente
        """
        pass
    
    @abstractmethod
    async def restore_user(self, user_id: UUID) -> bool:
        """
        Restaura un usuario marcado como eliminado.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            bool: True si se restauró correctamente
        """
        pass
    
    @abstractmethod
    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de usuarios.
        
        Returns:
            Dict[str, Any]: Diccionario con estadísticas
        """
        pass
    
    @abstractmethod
    async def search_users(
        self, 
        query: str, 
        limit: int = 50
    ) -> List[User]:
        """
        Busca usuarios por texto en múltiples campos.
        
        Args:
            query: Texto de búsqueda
            limit: Límite de resultados
            
        Returns:
            List[User]: Lista de usuarios encontrados
        """
        pass
    
    @abstractmethod
    async def bulk_update_status(
        self, 
        user_ids: List[UUID], 
        new_status: UserStatus
    ) -> int:
        """
        Actualiza el estado de múltiples usuarios.
        
        Args:
            user_ids: Lista de IDs de usuarios
            new_status: Nuevo estado
            
        Returns:
            int: Número de usuarios actualizados
        """
        pass
    
    @abstractmethod
    async def get_users_with_expired_subscriptions(self) -> List[User]:
        """
        Obtiene usuarios con suscripciones expiradas.
        
        Returns:
            List[User]: Lista de usuarios con suscripciones expiradas
        """
        pass
    
    @abstractmethod
    async def get_users_for_notification(
        self, 
        notification_type: str
    ) -> List[User]:
        """
        Obtiene usuarios que deben recibir un tipo específico de notificación.
        
        Args:
            notification_type: Tipo de notificación
            
        Returns:
            List[User]: Lista de usuarios para notificar
        """
        pass