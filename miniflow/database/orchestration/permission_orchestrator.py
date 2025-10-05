from typing import Dict, Any, List, Optional

from miniflow.database.enums import Roles
from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class PermissionOrchestrator(BaseOrchestrator):
    """
    Central RBAC (Role-Based Access Control) orchestrator for managing all junction tables.
    
    Manages permissions across all resources:
    - Workflows (UserWorkflowRole)
    - Files (UserFileRole)
    - Environment Variables (UserEnvarRole)
    - Executions (UserExecutionRole)
    
    Provides unified interface for:
    - User permission management
    - Resource access control
    - Audit trail queries
    - Bulk operations
    """

    def _get_primary_crud(self):
        return self.permission_crud

    @with_orchestration_errors('get_user_permissions')
    @with_session
    def get_user_permissions(self, session, user_id: str) -> Dict[str, Any]:
        """
        Kullanıcının tüm kaynaklardaki izinlerini listeler.
        
        Kullanım Amacı:
            - Admin panel: Kullanıcı detay sayfası
            - User dashboard: Kullanıcının erişebildiği kaynakları gösterme
            - Permission audit: Kullanıcının toplam yetki seviyesini kontrol
        
        Args:
            user_id: İzinleri listelenecek kullanıcının ID'si
        
        Returns:
            Dict containing:
                - user_id: Kullanıcı ID
                - workflows: Workflow izinleri listesi
                - files: File izinleri listesi
                - environment_variables: Envar izinleri listesi
                - executions: Execution izinleri listesi
                - total_permissions: Toplam izin sayısı
        
        Example:
            >>> result = permission_orch.get_user_permissions(user_id="USR_123")
            >>> print(f"User has {result['total_permissions']} permissions")
            >>> print(f"Workflows: {len(result['workflows'])}")
        """
        self._validate_user_exist(session, user_id)
        
        workflows = self.user_workflow_role_crud._get_all(session, user_id=user_id, limit=1000)
        files = self.user_file_role_crud._get_all(session, user_id=user_id, limit=1000)
        envars = self.user_envar_role_crud._get_all(session, user_id=user_id, limit=1000)
        executions = self.user_execution_role_crud._get_all(session, user_id=user_id, limit=1000)
        
        return {
            'user_id': user_id,
            'workflows': self._serialize_list_result(workflows, len(workflows)),
            'files': self._serialize_list_result(files, len(files)),
            'environment_variables': self._serialize_list_result(envars, len(envars)),
            'executions': self._serialize_list_result(executions, len(executions)),
            'total_permissions': len(workflows) + len(files) + len(envars) + len(executions)
        }

    @with_orchestration_errors('get_resource_users')
    @with_session
    def get_resource_users(self, session, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Bir kaynağa erişimi olan tüm kullanıcıları ve rollerini listeler.
        
        Kullanım Amacı:
            - Workflow/File paylaşım ekranı
            - Access control yönetimi
            - Collaboration: Kimlerle çalışıldığını görme
            - Permission review: Kaynak güvenliğini kontrol
        
        Args:
            resource_type: Kaynak tipi ('workflow', 'file', 'envar', 'execution')
            resource_id: Kaynak ID'si
        
        Returns:
            Dict containing:
                - resource_type: Kaynak tipi
                - resource_id: Kaynak ID
                - users: Kullanıcılar ve rolleri listesi
                - total_users: Toplam kullanıcı sayısı
        
        Example:
            >>> users = permission_orch.get_resource_users(
            ...     resource_type="workflow",
            ...     resource_id="WF_456"
            ... )
            >>> for user in users['users']:
            ...     print(f"{user['user_id']}: {user['role']}")
        """
        resource_type = resource_type.lower()
        
        if resource_type == 'workflow':
            self._validate_workflow_exist(session, resource_id)
            users = self.user_workflow_role_crud._get_all(session, workflow_id=resource_id, limit=1000)
        elif resource_type == 'file':
            self._validate_file_exist(session, resource_id)
            users = self.user_file_role_crud._get_all(session, file_id=resource_id, limit=1000)
        elif resource_type == 'envar':
            self._validate_envar_exist(session, resource_id)
            users = self.user_envar_role_crud._get_all(session, envar_id=resource_id, limit=1000)
        elif resource_type == 'execution':
            self._validate_execution_exist(session, resource_id)
            users = self.user_execution_role_crud._get_all(session, execution_id=resource_id, limit=1000)
        else:
            raise ValueError(f"Invalid resource_type: {resource_type}. Must be one of: workflow, file, envar, execution")
        
        return {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'users': self._serialize_list_result(users, len(users)),
            'total_users': len(users)
        }

    @with_orchestration_errors('check_permission')
    @with_session
    def check_permission(self, session, user_id: str, resource_type: str, resource_id: str, required_role: Optional[Roles] = None) -> Dict[str, Any]:
        """
        Kullanıcının bir kaynağa erişim yetkisini ve rol seviyesini kontrol eder.
        
        Kullanım Amacı:
            - API middleware: Route-level access control
            - Frontend: UI elementlerini gösterme/gizleme
            - Business logic: Operasyon öncesi yetki kontrolü
            - Security: Unauthorized access prevention
        
        Args:
            user_id: Kontrol edilecek kullanıcının ID'si
            resource_type: Kaynak tipi ('workflow', 'file', 'envar', 'execution')
            resource_id: Kaynak ID'si
            required_role: (Optional) Gerekli minimum rol seviyesi
        
        Returns:
            Dict containing:
                - user_id: Kullanıcı ID
                - resource_type: Kaynak tipi
                - resource_id: Kaynak ID
                - has_access: Erişim var mı? (bool)
                - role: Kullanıcının rolü (str)
                - required_role: İstenen rol (str, if provided)
                - meets_requirement: Yeterli yetkiye sahip mi? (bool)
        
        Example:
            >>> # Basit erişim kontrolü
            >>> perm = permission_orch.check_permission(
            ...     user_id="USR_123",
            ...     resource_type="workflow",
            ...     resource_id="WF_456"
            ... )
            >>> if not perm['has_access']:
            ...     raise PermissionError("Access denied")
            
            >>> # Rol seviyesi kontrolü
            >>> perm = permission_orch.check_permission(
            ...     user_id="USR_123",
            ...     resource_type="workflow",
            ...     resource_id="WF_456",
            ...     required_role=Roles.EDITOR
            ... )
            >>> if not perm['meets_requirement']:
            ...     raise PermissionError("EDITOR role required")
        """
        self._validate_user_exist(session, user_id)
        resource_type = resource_type.lower()
        
        if resource_type == 'workflow':
            self._validate_workflow_exist(session, resource_id)
            role_record = self.user_workflow_role_crud._get_by_user_and_resource(session, user_id, resource_id)
        elif resource_type == 'file':
            self._validate_file_exist(session, resource_id)
            role_record = self.user_file_role_crud._get_by_user_and_resource(session, user_id, resource_id)
        elif resource_type == 'envar':
            self._validate_envar_exist(session, resource_id)
            role_record = self.user_envar_role_crud._get_by_user_and_resource(session, user_id, resource_id)
        elif resource_type == 'execution':
            self._validate_execution_exist(session, resource_id)
            role_record = self.user_execution_role_crud._get_by_user_and_resource(session, user_id, resource_id)
        else:
            raise ValueError(f"Invalid resource_type: {resource_type}")
        
        has_access = role_record is not None
        user_role = role_record.role if has_access else None
        
        from .base_orchestrator import ROLE_HIERARCHY
        meets_requirement = False
        if has_access and required_role:
            meets_requirement = ROLE_HIERARCHY.get(user_role, -1) >= ROLE_HIERARCHY.get(required_role, 0)
        
        return {
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'has_access': has_access,
            'role': user_role.value if user_role else None,
            'required_role': required_role.value if required_role else None,
            'meets_requirement': meets_requirement if required_role else has_access
        }

    @with_orchestration_errors('grant_permission')
    @with_session
    def grant_permission(self, session, user_id: str, resource_type: str, resource_id: str, role: Roles, granted_by: str) -> Dict[str, Any]:
        """
        Kullanıcıya bir kaynak üzerinde belirli bir rol ile izin verir.
        
        Kullanım Amacı:
            - Collaboration: Takım üyelerini projeye ekleme
            - Workflow paylaşımı: Başkalarına erişim verme
            - Team management: Rol atama
            - Delegation: Yetki devri
        
        Gereksinim:
            - granted_by kullanıcısının OWNER rolü olmalı
        
        Args:
            user_id: İzin verilecek kullanıcının ID'si
            resource_type: Kaynak tipi ('workflow', 'file', 'envar', 'execution')
            resource_id: Kaynak ID'si
            role: Verilecek rol (VIEWER, CONTRIBUTOR, EDITOR, OWNER)
            granted_by: İzni veren kullanıcının ID'si (OWNER olmalı)
        
        Returns:
            Dict: Oluşturulan permission kaydı
        
        Raises:
            PermissionError: granted_by OWNER değilse
            ValidationError: Kullanıcı veya kaynak bulunamazsa
        
        Example:
            >>> # Kullanıcıyı EDITOR olarak ekle
            >>> result = permission_orch.grant_permission(
            ...     user_id="USR_BOB",
            ...     resource_type="workflow",
            ...     resource_id="WF_456",
            ...     role=Roles.EDITOR,
            ...     granted_by="USR_ALICE"  # OWNER olmalı
            ... )
            >>> # Bob artık workflow'u düzenleyebilir
        """
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, granted_by)
        resource_type = resource_type.lower()
        
        if resource_type == 'workflow':
            self._validate_workflow_exist(session, resource_id)
            result = self.user_workflow_role_crud._add_user(session, resource_id, user_id, role, granted_by)
        elif resource_type == 'file':
            self._validate_file_exist(session, resource_id)
            result = self.user_file_role_crud._add_user(session, resource_id, user_id, role, granted_by)
        elif resource_type == 'envar':
            self._validate_envar_exist(session, resource_id)
            result = self.user_envar_role_crud._add_user(session, resource_id, user_id, role, granted_by)
        elif resource_type == 'execution':
            self._validate_execution_exist(session, resource_id)
            result = self.user_execution_role_crud._add_user(session, resource_id, user_id, role, granted_by)
        else:
            raise ValueError(f"Invalid resource_type: {resource_type}")
        
        return self._serialize_single_result(result)

    @with_orchestration_errors('revoke_permission')
    @with_session
    def revoke_permission(self, session, user_id: str, resource_type: str, resource_id: str, revoked_by: str) -> Dict[str, Any]:
        """
        Kullanıcının bir kaynak üzerindeki iznini iptal eder.
        
        Kullanım Amacı:
            - Team member removal: Takımdan çıkarma
            - Access revocation: Erişim iptali
            - Security: Güvenlik ihlali durumunda hızlı erişim engelleme
            - Project cleanup: Eski kullanıcıları temizleme
        
        Gereksinim:
            - revoked_by kullanıcısının OWNER rolü olmalı
            - Son OWNER çıkarılamaz (güvenlik)
        
        Args:
            user_id: İzni iptal edilecek kullanıcının ID'si
            resource_type: Kaynak tipi ('workflow', 'file', 'envar', 'execution')
            resource_id: Kaynak ID'si
            revoked_by: İzni iptal eden kullanıcının ID'si (OWNER olmalı)
        
        Returns:
            Dict containing:
                - deleted: Başarılı mı? (bool)
                - user_id: Kullanıcı ID
                - resource_type: Kaynak tipi
                - resource_id: Kaynak ID
        
        Raises:
            PermissionError: revoked_by OWNER değilse veya son OWNER çıkarılmaya çalışılıyorsa
            ValidationError: Kullanıcı veya kaynak bulunamazsa
        
        Example:
            >>> # Kullanıcının erişimini iptal et
            >>> result = permission_orch.revoke_permission(
            ...     user_id="USR_BOB",
            ...     resource_type="workflow",
            ...     resource_id="WF_456",
            ...     revoked_by="USR_ALICE"  # OWNER olmalı
            ... )
            >>> # Bob artık workflow'a erişemez
        """
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, revoked_by)
        resource_type = resource_type.lower()
        
        if resource_type == 'workflow':
            self._validate_workflow_exist(session, resource_id)
            success = self.user_workflow_role_crud._remove_user(session, resource_id, user_id, revoked_by)
        elif resource_type == 'file':
            self._validate_file_exist(session, resource_id)
            success = self.user_file_role_crud._remove_user(session, resource_id, user_id, revoked_by)
        elif resource_type == 'envar':
            self._validate_envar_exist(session, resource_id)
            success = self.user_envar_role_crud._remove_user(session, resource_id, user_id, revoked_by)
        elif resource_type == 'execution':
            self._validate_execution_exist(session, resource_id)
            success = self.user_execution_role_crud._remove_user(session, resource_id, user_id, revoked_by)
        else:
            raise ValueError(f"Invalid resource_type: {resource_type}")
        
        return {
            'deleted': success,
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id
        }

    @with_orchestration_errors('update_permission')
    @with_session
    def update_permission(self, session, user_id: str, resource_type: str, resource_id: str, new_role: Roles, updated_by: str) -> Dict[str, Any]:
        """
        Kullanıcının bir kaynak üzerindeki rolünü günceller.
        
        Kullanım Amacı:
            - Role promotion: Rol yükseltme (VIEWER → EDITOR)
            - Role demotion: Rol düşürme (EDITOR → VIEWER)
            - Permission adjustment: Yetki seviyesi ayarlama
            - Team restructuring: Takım yapısı değişikliği
        
        Gereksinim:
            - updated_by kullanıcısının OWNER rolü olmalı
            - Son OWNER'ın rolü düşürülemez
        
        Args:
            user_id: Rolü güncellenecek kullanıcının ID'si
            resource_type: Kaynak tipi ('workflow', 'file', 'envar', 'execution')
            resource_id: Kaynak ID'si
            new_role: Yeni rol (VIEWER, CONTRIBUTOR, EDITOR, OWNER)
            updated_by: Güncellemeyi yapan kullanıcının ID'si (OWNER olmalı)
        
        Returns:
            Dict: Güncellenmiş permission kaydı
        
        Raises:
            PermissionError: updated_by OWNER değilse veya son OWNER düşürülmeye çalışılıyorsa
            ValidationError: Kullanıcı veya kaynak bulunamazsa
        
        Example:
            >>> # Kullanıcının rolünü EDITOR'dan VIEWER'a düşür
            >>> result = permission_orch.update_permission(
            ...     user_id="USR_BOB",
            ...     resource_type="workflow",
            ...     resource_id="WF_456",
            ...     new_role=Roles.VIEWER,
            ...     updated_by="USR_ALICE"  # OWNER olmalı
            ... )
            >>> # Bob artık sadece görüntüleyebilir
        """
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, updated_by)
        resource_type = resource_type.lower()
        
        if resource_type == 'workflow':
            self._validate_workflow_exist(session, resource_id)
            result = self.user_workflow_role_crud._update_user_role(session, resource_id, user_id, new_role, updated_by)
        elif resource_type == 'file':
            self._validate_file_exist(session, resource_id)
            result = self.user_file_role_crud._update_user_role(session, resource_id, user_id, new_role, updated_by)
        elif resource_type == 'envar':
            self._validate_envar_exist(session, resource_id)
            result = self.user_envar_role_crud._update_user_role(session, resource_id, user_id, new_role, updated_by)
        elif resource_type == 'execution':
            self._validate_execution_exist(session, resource_id)
            result = self.user_execution_role_crud._update_user_role(session, resource_id, user_id, new_role, updated_by)
        else:
            raise ValueError(f"Invalid resource_type: {resource_type}")
        
        return self._serialize_single_result(result)

    @with_orchestration_errors('transfer_ownership')
    @with_session
    def transfer_ownership(self, session, resource_type: str, resource_id: str, current_owner_id: str, new_owner_id: str) -> Dict[str, Any]:
        """
        Kaynak ownership'ini bir kullanıcıdan diğerine transfer eder.
        
        Kullanım Amacı:
            - Team lead change: Proje lideri değişimi
            - Responsibility delegation: Sorumluluk devri
            - Employee departure: Çalışan ayrılışı
            - Project handover: Proje devir
        
        İşlem:
            - Eski owner: OWNER → EDITOR
            - Yeni owner: Mevcut rol → OWNER
            - Atomic operation (ikisi birden güncellenir)
        
        Args:
            resource_type: Kaynak tipi ('workflow', 'file', 'envar', 'execution')
            resource_id: Kaynak ID'si
            current_owner_id: Mevcut OWNER'ın ID'si
            new_owner_id: Yeni OWNER olacak kullanıcının ID'si
        
        Returns:
            Dict: Transfer sonucu ve güncellenmiş kayıtlar
        
        Raises:
            PermissionError: current_owner gerçekten OWNER değilse
            ValidationError: Kullanıcılar veya kaynak bulunamazsa
        
        Example:
            >>> # Alice'den Bob'a ownership transfer
            >>> result = permission_orch.transfer_ownership(
            ...     resource_type="workflow",
            ...     resource_id="WF_456",
            ...     current_owner_id="USR_ALICE",
            ...     new_owner_id="USR_BOB"
            ... )
            >>> # Alice: OWNER → EDITOR
            >>> # Bob: EDITOR → OWNER
        """
        self._validate_user_exist(session, current_owner_id)
        self._validate_user_exist(session, new_owner_id)
        resource_type = resource_type.lower()
        
        if resource_type == 'workflow':
            self._validate_workflow_exist(session, resource_id)
            result = self.user_workflow_role_crud._transfer_ownership(session, resource_id, current_owner_id, new_owner_id)
        elif resource_type == 'file':
            self._validate_file_exist(session, resource_id)
            result = self.user_file_role_crud._transfer_ownership(session, resource_id, current_owner_id, new_owner_id)
        elif resource_type == 'envar':
            self._validate_envar_exist(session, resource_id)
            result = self.user_envar_role_crud._transfer_ownership(session, resource_id, current_owner_id, new_owner_id)
        elif resource_type == 'execution':
            self._validate_execution_exist(session, resource_id)
            result = self.user_execution_role_crud._transfer_ownership(session, resource_id, current_owner_id, new_owner_id)
        else:
            raise ValueError(f"Invalid resource_type: {resource_type}")
        
        return result

    @with_orchestration_errors('revoke_all_non_owners')
    @with_session
    def revoke_all_non_owners(self, session, resource_type: str, resource_id: str, revoked_by: str) -> Dict[str, Any]:
        """
        OWNER dışındaki tüm kullanıcıların erişimini iptal eder.
        
        Kullanım Amacı:
            - Security cleanup: Güvenlik temizliği
            - Project archiving: Proje arşivleme
            - Access restriction: Erişim kısıtlama
            - Privacy mode: Gizlilik modu (sadece owner)
            - Emergency lockdown: Acil durum kilitleme
        
        Gereksinim:
            - revoked_by kullanıcısının OWNER rolü olmalı
            - OWNER(s) korunur, silinmez
        
        Args:
            resource_type: Kaynak tipi ('workflow', 'file', 'envar', 'execution')
            resource_id: Kaynak ID'si
            revoked_by: İşlemi yapan kullanıcının ID'si (OWNER olmalı)
        
        Returns:
            Dict: İptal edilen kayıt sayısı ve sonuç
        
        Raises:
            PermissionError: revoked_by OWNER değilse
            ValidationError: Kaynak bulunamazsa
        
        Example:
            >>> # Tüm non-owner'ları çıkar
            >>> result = permission_orch.revoke_all_non_owners(
            ...     resource_type="workflow",
            ...     resource_id="WF_SENSITIVE",
            ...     revoked_by="USR_ALICE"  # OWNER olmalı
            ... )
            >>> # Sadece OWNER(s) kalır
        """
        self._validate_user_exist(session, revoked_by)
        resource_type = resource_type.lower()
        
        if resource_type == 'workflow':
            self._validate_workflow_exist(session, resource_id)
            result = self.user_workflow_role_crud._revoke_all_non_owners(session, resource_id, revoked_by)
        elif resource_type == 'file':
            self._validate_file_exist(session, resource_id)
            result = self.user_file_role_crud._revoke_all_non_owners(session, resource_id, revoked_by)
        elif resource_type == 'envar':
            self._validate_envar_exist(session, resource_id)
            result = self.user_envar_role_crud._revoke_all_non_owners(session, resource_id, revoked_by)
        elif resource_type == 'execution':
            self._validate_execution_exist(session, resource_id)
            result = self.user_execution_role_crud._revoke_all_non_owners(session, resource_id, revoked_by)
        else:
            raise ValueError(f"Invalid resource_type: {resource_type}")
        
        return result

    @with_orchestration_errors('bulk_grant_permissions')
    @with_session
    def bulk_grant_permissions(self, session, permissions: List[Dict[str, Any]], granted_by: str) -> Dict[str, Any]:
        """
        Birden fazla kullanıcıya toplu izin verir (batch operation).
        
        Kullanım Amacı:
            - Team onboarding: Yeni takım üyelerini toplu ekleme
            - Project sharing: Projeyi birden fazla kişiyle paylaşma
            - Batch user management: Toplu kullanıcı yönetimi
            - Migration: Eski sistemden izin aktarımı
        
        Avantajlar:
            - Tek transaction: Tümü başarılı veya tümü geri alınır
            - Performance: Tek seferde çok sayıda izin
            - Error handling: Başarısız olanlar raporlanır
        
        Args:
            permissions: İzin listesi, her biri şunları içermeli:
                - user_id: Kullanıcı ID
                - resource_type: Kaynak tipi
                - resource_id: Kaynak ID
                - role: Verilecek rol
            granted_by: İzni veren kullanıcının ID'si (OWNER olmalı)
        
        Returns:
            Dict containing:
                - granted: Başarılı izin sayısı
                - failed: Başarısız izin sayısı
                - total: Toplam izin sayısı
                - results: Başarılı sonuçlar listesi
                - errors: Hata detayları listesi
        
        Example:
            >>> # Yeni takımı projeye ekle
            >>> permissions = [
            ...     {'user_id': 'USR_001', 'resource_type': 'workflow', 
            ...      'resource_id': 'WF_A', 'role': Roles.EDITOR},
            ...     {'user_id': 'USR_002', 'resource_type': 'workflow',
            ...      'resource_id': 'WF_B', 'role': Roles.VIEWER},
            ... ]
            >>> result = permission_orch.bulk_grant_permissions(
            ...     permissions=permissions,
            ...     granted_by="USR_ADMIN"
            ... )
            >>> print(f"Granted: {result['granted']}, Failed: {result['failed']}")
        """
        self._validate_user_exist(session, granted_by)
        
        results = []
        errors = []
        
        for perm in permissions:
            try:
                result = self.grant_permission(
                    session,
                    user_id=perm['user_id'],
                    resource_type=perm['resource_type'],
                    resource_id=perm['resource_id'],
                    role=perm['role'],
                    granted_by=granted_by
                )
                results.append(result)
            except Exception as e:
                errors.append({
                    'permission': perm,
                    'error': str(e)
                })
        
        return {
            'granted': len(results),
            'failed': len(errors),
            'total': len(permissions),
            'results': results,
            'errors': errors
        }

    @with_orchestration_errors('bulk_revoke_permissions')
    @with_session
    def bulk_revoke_permissions(self, session, permissions: List[Dict[str, Any]], revoked_by: str) -> Dict[str, Any]:
        """
        Birden fazla kullanıcının iznini toplu iptal eder (batch operation).
        
        Kullanım Amacı:
            - Team offboarding: Takım üyelerini toplu çıkarma
            - Project archiving: Proje arşivlenirken erişim temizliği
            - Access cleanup: Toplu erişim temizliği
            - Security incident: Güvenlik olayında toplu erişim iptali
        
        Avantajlar:
            - Tek transaction: Tümü başarılı veya tümü geri alınır
            - Performance: Tek seferde çok sayıda iptal
            - Error handling: Başarısız olanlar raporlanır
        
        Args:
            permissions: İptal edilecek izinler, her biri şunları içermeli:
                - user_id: Kullanıcı ID
                - resource_type: Kaynak tipi
                - resource_id: Kaynak ID
            revoked_by: İşlemi yapan kullanıcının ID'si (OWNER olmalı)
        
        Returns:
            Dict containing:
                - revoked: Başarılı iptal sayısı
                - failed: Başarısız iptal sayısı
                - total: Toplam istek sayısı
                - results: Başarılı sonuçlar listesi
                - errors: Hata detayları listesi
        
        Example:
            >>> # Eski takım üyelerini çıkar
            >>> permissions = [
            ...     {'user_id': 'USR_001', 'resource_type': 'workflow', 'resource_id': 'WF_A'},
            ...     {'user_id': 'USR_002', 'resource_type': 'workflow', 'resource_id': 'WF_B'},
            ... ]
            >>> result = permission_orch.bulk_revoke_permissions(
            ...     permissions=permissions,
            ...     revoked_by="USR_ADMIN"
            ... )
            >>> print(f"Revoked: {result['revoked']}, Failed: {result['failed']}")
        """
        self._validate_user_exist(session, revoked_by)
        
        results = []
        errors = []
        
        for perm in permissions:
            try:
                result = self.revoke_permission(
                    session,
                    user_id=perm['user_id'],
                    resource_type=perm['resource_type'],
                    resource_id=perm['resource_id'],
                    revoked_by=revoked_by
                )
                results.append(result)
            except Exception as e:
                errors.append({
                    'permission': perm,
                    'error': str(e)
                })
        
        return {
            'revoked': len(results),
            'failed': len(errors),
            'total': len(permissions),
            'results': results,
            'errors': errors
        }

    @with_orchestration_errors('get_user_owned_resources')
    @with_session
    def get_user_owned_resources(self, session, user_id: str) -> Dict[str, Any]:
        """
        Kullanıcının OWNER olduğu tüm kaynakları listeler.
        
        Kullanım Amacı:
            - User dashboard: "Sahip olduğum projeler"
            - Admin panel: Ownership tracking
            - Responsibility audit: Sorumluluk kontrolü
            - Transfer planning: Ownership transfer planlaması
            - Resource management: Kaynak yönetimi
        
        Args:
            user_id: Sorgulanacak kullanıcının ID'si
        
        Returns:
            Dict containing:
                - user_id: Kullanıcı ID
                - owned_workflows: OWNER olunan workflow'lar
                - owned_files: OWNER olunan file'lar
                - owned_envars: OWNER olunan envar'lar
                - owned_executions: OWNER olunan execution'lar
                - total_owned: Toplam sahip olunan kaynak sayısı
        
        Example:
            >>> # Kullanıcının sahip olduğu kaynakları göster
            >>> owned = permission_orch.get_user_owned_resources(user_id="USR_ALICE")
            >>> print(f"Alice owns:")
            >>> print(f"  - {len(owned['owned_workflows'])} workflows")
            >>> print(f"  - {len(owned['owned_files'])} files")
            >>> print(f"  - Total: {owned['total_owned']} resources")
        """
        self._validate_user_exist(session, user_id)
        
        workflows = self.user_workflow_role_crud._get_all(session, user_id=user_id, role=Roles.OWNER, limit=1000)
        files = self.user_file_role_crud._get_all(session, user_id=user_id, role=Roles.OWNER, limit=1000)
        envars = self.user_envar_role_crud._get_all(session, user_id=user_id, role=Roles.OWNER, limit=1000)
        executions = self.user_execution_role_crud._get_all(session, user_id=user_id, role=Roles.OWNER, limit=1000)
        
        return {
            'user_id': user_id,
            'owned_workflows': self._serialize_list_result(workflows, len(workflows)),
            'owned_files': self._serialize_list_result(files, len(files)),
            'owned_envars': self._serialize_list_result(envars, len(envars)),
            'owned_executions': self._serialize_list_result(executions, len(executions)),
            'total_owned': len(workflows) + len(files) + len(envars) + len(executions)
        }

    @with_orchestration_errors('get_permission_audit_trail')
    @with_session
    def get_permission_audit_trail(self, session, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Bir kaynağın tüm izin geçmişini ve değişikliklerini listeler (audit log).
        
        Kullanım Amacı:
            - Compliance audit: Yasal uyumluluk kontrolü
            - Security investigation: Güvenlik soruşturması
            - Change tracking: Kim ne zaman ne değiştirdi?
            - Access history: Erişim geçmişi
            - Forensics: Güvenlik olayı sonrası inceleme
        
        Özellikler:
            - Tarih sıralı: En yeniden en eskiye
            - Full audit trail: granted_by, granted_at, updated_by, updated_at
            - Historical data: Geçmiş değişiklikler
        
        Args:
            resource_type: Kaynak tipi ('workflow', 'file', 'envar', 'execution')
            resource_id: Kaynak ID'si
        
        Returns:
            Dict containing:
                - resource_type: Kaynak tipi
                - resource_id: Kaynak ID
                - audit_trail: İzin geçmişi listesi (tarih sıralı)
                - total_records: Toplam kayıt sayısı
        
        Example:
            >>> # Critical workflow için audit log
            >>> trail = permission_orch.get_permission_audit_trail(
            ...     resource_type="workflow",
            ...     resource_id="WF_CRITICAL"
            ... )
            >>> print("Permission History:")
            >>> for entry in trail['audit_trail']:
            ...     print(f"{entry['updated_at']}: {entry['user_id']} "
            ...           f"granted {entry['role']} by {entry['granted_by']}")
        """
        resource_type = resource_type.lower()
        
        if resource_type == 'workflow':
            self._validate_workflow_exist(session, resource_id)
            permissions = self.user_workflow_role_crud._get_all(
                session, 
                workflow_id=resource_id, 
                limit=1000,
                order_by='updated_at',
                order_desc=True
            )
        elif resource_type == 'file':
            self._validate_file_exist(session, resource_id)
            permissions = self.user_file_role_crud._get_all(
                session,
                file_id=resource_id,
                limit=1000,
                order_by='updated_at',
                order_desc=True
            )
        elif resource_type == 'envar':
            self._validate_envar_exist(session, resource_id)
            permissions = self.user_envar_role_crud._get_all(
                session,
                envar_id=resource_id,
                limit=1000,
                order_by='updated_at',
                order_desc=True
            )
        elif resource_type == 'execution':
            self._validate_execution_exist(session, resource_id)
            permissions = self.user_execution_role_crud._get_all(
                session,
                execution_id=resource_id,
                limit=1000,
                order_by='updated_at',
                order_desc=True
            )
        else:
            raise ValueError(f"Invalid resource_type: {resource_type}")
        
        return {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'audit_trail': self._serialize_list_result(permissions, len(permissions)),
            'total_records': len(permissions)
        }

