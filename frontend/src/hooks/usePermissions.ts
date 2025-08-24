// Permissions hook
import { useState, useCallback, useEffect, useMemo } from 'react';
import { type UsePermissionsReturn, type Permission, type Role, type PermissionCheck, type UserPermissions } from './types';
import config from '../config';
import useAuth from './useAuth';
import useApi from './useApi';

interface UsePermissionsOptions {
  autoFetch?: boolean;
  cachePermissions?: boolean;
  enableRoleHierarchy?: boolean;
}

const usePermissions = (
  options: UsePermissionsOptions = {}
): UsePermissionsReturn => {
  const {
    autoFetch = true,
    cachePermissions = true,
    enableRoleHierarchy = true,
  } = options;

  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [userPermissions] = useState<UserPermissions | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const { user } = useAuth();
  const { execute: apiExecute } = useApi(() => Promise.resolve({}));

  // Role hierarchy definition
  const roleHierarchy = useMemo((): Record<string, string[]> => ({
    'super_admin': ['admin', 'manager', 'user', 'guest'],
    'admin': ['manager', 'user', 'guest'],
    'manager': ['user', 'guest'],
    'user': ['guest'],
    'guest': [],
  }), []);

  // Fetch user permissions
  const fetchPermissions = useCallback(async () => {
    if (!user) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiExecute({
        url: `${config.api.ENDPOINTS.PERMISSIONS.USER}/${user.id}`,
        method: 'GET',
      });

      setPermissions((response as any)?.data?.permissions || []);
      setRoles((response as any)?.data?.roles || []);
      setLastUpdated(new Date());

      // Cache permissions if enabled
      if (cachePermissions) {
        localStorage.setItem(
          `permissions_${user.id}`,
          JSON.stringify({
            permissions: (response as any)?.data?.permissions || [],
            roles: (response as any)?.data?.roles || [],
            timestamp: new Date().toISOString(),
          })
        );
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch permissions';
      setError(errorMessage);
      console.error('Permissions fetch error:', err);

      // Try to load from cache if available
      if (cachePermissions) {
        const cached = localStorage.getItem(`permissions_${user.id}`);
        if (cached) {
          try {
            const { permissions: cachedPermissions, roles: cachedRoles } = JSON.parse(cached);
            setPermissions(cachedPermissions);
            setRoles(cachedRoles);
          } catch (cacheError) {
            console.error('Failed to load cached permissions:', cacheError);
          }
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, [user, cachePermissions]); // Removed apiExecute to prevent infinite loop

  // Check if user has specific permission
  const hasPermission = useCallback((permission: string): boolean => {
    if (!user || !permissions.length) return false;

    // Super admin has all permissions
    if (user.role === 'super_admin') return true;

    // Check direct permissions
    const hasDirectPermission = permissions.some(p => 
      p.name === permission && p.granted
    );

    if (hasDirectPermission) return true;

    // Check role-based permissions if hierarchy is enabled
    if (enableRoleHierarchy && user.role) {
      const userRoleHierarchy = roleHierarchy[user.role as keyof typeof roleHierarchy] || [];
      
      // Check if any role in hierarchy has the permission
      return roles.some(role => 
        (role.name === user.role || userRoleHierarchy.includes(role.name)) &&
        role.permissions.includes(permission)
      );
    }

    return false;
  }, [user, permissions, roles, enableRoleHierarchy, roleHierarchy]);

  // Check multiple permissions (AND logic)
  const hasAllPermissions = useCallback((permissionList: string[]): boolean => {
    return permissionList.every(permission => hasPermission(permission));
  }, [hasPermission]);

  // Check multiple permissions (OR logic)
  const hasAnyPermission = useCallback((permissionList: string[]): boolean => {
    return permissionList.some(permission => hasPermission(permission));
  }, [hasPermission]);

  // Check if user has specific role
  const hasRole = useCallback((roleName: string): boolean => {
    if (!user) return false;

    // Check direct role
    if (user.role === roleName) return true;

    // Check role hierarchy if enabled
    if (enableRoleHierarchy && user.role) {
      const userRoleHierarchy = roleHierarchy[user.role as keyof typeof roleHierarchy] || [];
      return userRoleHierarchy.includes(roleName);
    }

    return false;
  }, [user, enableRoleHierarchy, roleHierarchy]);

  // Check multiple roles (OR logic)
  const hasAnyRole = useCallback((roleList: string[]): boolean => {
    return roleList.some(role => hasRole(role));
  }, [hasRole]);

  // Get user's effective permissions (including inherited from roles)
  const getEffectivePermissions = useCallback((): string[] => {
    if (!user || !permissions.length) return [];

    const effectivePermissions = new Set<string>();

    // Add direct permissions
    permissions.forEach(permission => {
      if (permission.granted) {
        effectivePermissions.add(permission.name);
      }
    });

    // Add role-based permissions
    if (enableRoleHierarchy && user.role) {
      const userRoleHierarchy = [user.role, ...(roleHierarchy[user.role as keyof typeof roleHierarchy] || [])];
      
      roles.forEach(role => {
        if (userRoleHierarchy.includes(role.name)) {
          role.permissions.forEach(permissionName => {
            effectivePermissions.add(permissionName);
          });
        }
      });
    }

    return Array.from(effectivePermissions);
  }, [user, permissions, roles, enableRoleHierarchy, roleHierarchy]);

  // Get permissions by category
  const getPermissionsByCategory = useCallback((category: string): Permission[] => {
    return permissions.filter(p => p.category === category && p.granted);
  }, [permissions]);

  // Check permission with context
  const checkPermission = useCallback((check: PermissionCheck): boolean => {
    const { permission, resource, action, context } = check;

    // Basic permission check
    if (!hasPermission(permission)) return false;

    // Resource-based check
    if (resource && user) {
      // Check if user owns the resource
      if (resource.ownerId && resource.ownerId !== user.id) {
        // Check if user has admin permissions for this resource type
        const adminPermission = `${resource.type}:admin`;
        if (!hasPermission(adminPermission)) return false;
      }

      // Check resource-specific permissions
      if (resource.permissions) {
        const resourcePermission = `${resource.type}:${action}`;
        if (!resource.permissions.includes(resourcePermission)) return false;
      }
    }

    // Context-based checks
    if (context) {
      // Time-based restrictions
      if (context.timeRestrictions) {
        const now = new Date();
        const currentHour = now.getHours();
        const { startHour, endHour } = (context.timeRestrictions as any) || {};
        
        if (startHour !== undefined && endHour !== undefined) {
          if (currentHour < startHour || currentHour > endHour) {
            return false;
          }
        }
      }

      // IP-based restrictions
      if (context.ipRestrictions && context.currentIP) {
        const allowedIPs = context.ipRestrictions;
        if (!(allowedIPs as any).includes(context.currentIP)) {
          return false;
        }
      }

      // Custom validation
      if (context.customValidator) {
        return (context.customValidator as any)(user, check);
      }
    }

    return true;
  }, [hasPermission, user]);

  // Get user's role level (for hierarchy comparison)
  const getRoleLevel = useCallback((roleName?: string): number => {
    const role = roleName || user?.role;
    if (!role) return 0;

    const levels: Record<string, number> = {
      'guest': 1,
      'user': 2,
      'manager': 3,
      'admin': 4,
      'super_admin': 5,
    };

    return levels[role] || 0;
  }, [user]);

  // Check if user has higher or equal role level
  const hasRoleLevel = useCallback((role: string, level: number): boolean => {
    const roleLevel = getRoleLevel(role);
    return roleLevel >= level;
  }, [getRoleLevel]);

  // Check if user can perform action on resource
  const canPerformAction = useCallback((action: string, resourceType: string): boolean => {
    const permission = `${resourceType}:${action}`;
    
    if (!hasPermission(permission)) return false;

    return true;
  }, [hasPermission]);

  // Get available actions for resource type
  const getAvailableActions = useCallback((resourceType: string): string[] => {
    const resourcePermissions = permissions.filter(p => 
      p.name.startsWith(`${resourceType}:`) && p.granted
    );
    
    return resourcePermissions.map(p => p.name.split(':')[1]);
  }, [permissions]);

  // Clear permissions cache
  const clearCache = useCallback(() => {
    if (user && cachePermissions) {
      localStorage.removeItem(`permissions_${user.id}`);
    }
  }, [user, cachePermissions]);

  // Refresh permissions
  const refreshPermissions = useCallback(async () => {
    clearCache();
    await fetchPermissions();
  }, []); // Removed dependencies to prevent infinite loop

  // Auto-fetch permissions on mount and user change
  useEffect(() => {
    if (autoFetch && user) {
      fetchPermissions();
    }
  }, [autoFetch, user]); // Removed fetchPermissions to prevent infinite loop

  // Memoized permission checks for common operations
  const commonPermissions = useMemo(() => ({
    canReadCredentials: hasPermission('credentials:read'),
    canWriteCredentials: hasPermission('credentials:write'),
    canProcessCredentials: hasPermission('credentials:process'),
    canDeleteCredentials: hasPermission('credentials:delete'),
    canViewUsage: hasPermission('usage:read'),
    canManageApiKeys: hasPermission('api_keys:write'),
    canViewApiKeys: hasPermission('api_keys:read'),
    canManageUsers: hasPermission('users:write'),
    canViewUsers: hasPermission('users:read'),
    canManageSystem: hasPermission('system:admin'),
    isAdmin: hasAnyRole(['admin', 'super_admin']),
    isSuperAdmin: hasRole('super_admin'),
    isManager: hasAnyRole(['manager', 'admin', 'super_admin']),
  }), [hasPermission, hasRole, hasAnyRole]);

  // Additional functions implementation

  const checkPermissions = useCallback((checks: PermissionCheck[]): boolean[] => {
    return checks.map(check => checkPermission(check));
  }, [checkPermission]);

  const getRolePermissions = useCallback((roleId: string): Permission[] => {
    const role = roles.find(r => r.id === roleId);
    if (!role) return [];
    return permissions.filter(p => role.permissions.includes(p.name));
  }, [roles, permissions]);

  const getUserRoles = useCallback((): Role[] => {
    if (!userPermissions) return [];
    return roles.filter(role => (userPermissions as any).roles?.includes(role.id));
  }, [roles, userPermissions]);

  return {
    permissions,
    roles,
    userPermissions,
    isLoading,
    error,
    lastUpdated,
    fetchPermissions,
    hasPermission,
    hasAllPermissions,
    hasAnyPermission,
    hasRole,
    hasAnyRole,
    getEffectivePermissions,
    checkPermission,
    checkPermissions,
    getPermissionsByCategory,
    getRolePermissions,
    getUserRoles,
    getRoleLevel,
    hasRoleLevel,
    canPerformAction,
    getAvailableActions,
    clearCache,
    refreshPermissions,
    commonPermissions,
  };
};

// Permissions utilities
export const permissionsUtils = {
  // Parse permission string
  parsePermission: (permission: string): { resource: string; action: string } => {
    const [resource, action] = permission.split(':');
    return { resource: resource || '', action: action || '' };
  },

  // Create permission string
  createPermission: (resource: string, action: string): string => {
    return `${resource}:${action}`;
  },

  // Get permission categories
  getPermissionCategories: (permissions: Permission[]): string[] => {
    const categories = new Set(permissions.map(p => p.category).filter(Boolean));
    return Array.from(categories);
  },

  // Group permissions by category
  groupPermissionsByCategory: (permissions: Permission[]): Record<string, Permission[]> => {
    return permissions.reduce((groups, permission) => {
      const category = permission.category || 'uncategorized';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(permission);
      return groups;
    }, {} as Record<string, Permission[]>);
  },

  // Check if permission is granted
  isPermissionGranted: (permission: Permission): boolean => {
    return permission.granted === true;
  },

  // Filter granted permissions
  filterGrantedPermissions: (permissions: Permission[]): Permission[] => {
    return permissions.filter(p => p.granted);
  },

  // Get permission display name
  getPermissionDisplayName: (permission: string): string => {
    const displayNames: Record<string, string> = {
      'credentials:read': 'View Credentials',
      'credentials:write': 'Create/Edit Credentials',
      'credentials:process': 'Process Credentials',
      'credentials:delete': 'Delete Credentials',
      'usage:read': 'View Usage Statistics',
      'api_keys:read': 'View API Keys',
      'api_keys:write': 'Manage API Keys',
      'users:read': 'View Users',
      'users:write': 'Manage Users',
      'system:admin': 'System Administration',
    };

    return displayNames[permission] || permission;
  },

  // Get role display name
  getRoleDisplayName: (role: string): string => {
    const displayNames: Record<string, string> = {
      'guest': 'Guest',
      'user': 'User',
      'manager': 'Manager',
      'admin': 'Administrator',
      'super_admin': 'Super Administrator',
    };

    return displayNames[role] || role;
  },

  // Get role color
  getRoleColor: (role: string): string => {
    const colors: Record<string, string> = {
      'guest': 'gray',
      'user': 'blue',
      'manager': 'green',
      'admin': 'orange',
      'super_admin': 'red',
    };

    return colors[role] || 'gray';
  },

  // Validate permission format
  validatePermissionFormat: (permission: string): boolean => {
    const permissionRegex = /^[a-z_]+:[a-z_]+$/;
    return permissionRegex.test(permission);
  },

  // Get default permissions for role
  getDefaultPermissionsForRole: (role: string): string[] => {
    const defaultPermissions: Record<string, string[]> = {
      'guest': [
        'credentials:read',
      ],
      'user': [
        'credentials:read',
        'credentials:write',
        'credentials:process',
        'usage:read',
        'api_keys:read',
      ],
      'manager': [
        'credentials:read',
        'credentials:write',
        'credentials:process',
        'credentials:delete',
        'usage:read',
        'api_keys:read',
        'api_keys:write',
        'users:read',
      ],
      'admin': [
        'credentials:read',
        'credentials:write',
        'credentials:process',
        'credentials:delete',
        'usage:read',
        'api_keys:read',
        'api_keys:write',
        'users:read',
        'users:write',
      ],
      'super_admin': [
        'credentials:read',
        'credentials:write',
        'credentials:process',
        'credentials:delete',
        'usage:read',
        'api_keys:read',
        'api_keys:write',
        'users:read',
        'users:write',
        'system:admin',
      ],
    };

    return defaultPermissions[role] || [];
  },

  // Compare role levels
  compareRoles: (role1: string, role2: string): number => {
    const levels: Record<string, number> = {
      'guest': 1,
      'user': 2,
      'manager': 3,
      'admin': 4,
      'super_admin': 5,
    };

    const level1 = levels[role1] || 0;
    const level2 = levels[role2] || 0;

    return level1 - level2;
  },

  // Check if role can access resource
  canRoleAccessResource: (role: string, resourceType: string, action: string): boolean => {
    const defaultPermissions = permissionsUtils.getDefaultPermissionsForRole(role);
    const requiredPermission = `${resourceType}:${action}`;
    return defaultPermissions.includes(requiredPermission);
  },

  // Generate permission matrix
  generatePermissionMatrix: (roles: string[], permissions: string[]): Record<string, Record<string, boolean>> => {
    const matrix: Record<string, Record<string, boolean>> = {};

    roles.forEach(role => {
      matrix[role] = {};
      const rolePermissions = permissionsUtils.getDefaultPermissionsForRole(role);
      
      permissions.forEach(permission => {
        matrix[role][permission] = rolePermissions.includes(permission);
      });
    });

    return matrix;
  },
};

export default usePermissions;