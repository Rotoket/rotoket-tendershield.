"""
Kill Switch Manager — ШАГ 13

Управление Kill Switch и режимами работы системы.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from pathlib import Path

from kill_switch_types import (
    SystemMode,
    KillSwitchTrigger,
    KillSwitchActivation,
    KillSwitchStatus,
    SafeModeLimits,
)


class KillSwitchManager:
    """
    Управление Kill Switch и режимами работы системы.
    
    ⚠️ ВАЖНО: Kill Switch должен использоваться ТОЛЬКО в экстренных случаях!
    
    Kill Switch — это НЕ выключение системы.
    Это отключение LLM-reasoning слоя (ШАГ 4) с сохранением
    Evidence, Audit, Versioning и переводом в Safe Mode.
    
    Экстренные случаи для активации:
    - Критичные ошибки в LLM-анализе
    - Некорректные управленческие выводы
    - Проблемы с безопасностью или качеством данных
    - Временная остановка для обновления/проверки
    
    По умолчанию система работает в NORMAL режиме!
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Инициализация Kill Switch Manager.
        
        Args:
            config_path: Путь к файлу конфигурации (для персистентности)
        """
        self.config_path = Path(config_path) if config_path else Path("backend/kill_switch_state.json")
        self._status: KillSwitchStatus = KillSwitchStatus()
        self._load_status()
    
    def _load_status(self) -> None:
        """Загружает статус из файла (если существует)."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._status = KillSwitchStatus(**data)
            except Exception:
                # Если не удалось загрузить, используем дефолтный статус
                self._status = KillSwitchStatus()
    
    def _save_status(self) -> None:
        """Сохраняет статус в файл."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._status.dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Логируем ошибку, но не падаем
            print(f"[KillSwitchManager] Ошибка сохранения статуса: {e}")
    
    def activate(
        self,
        trigger: KillSwitchTrigger,
        reason: str,
        target_mode: SystemMode = SystemMode.SAFE,
        activated_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KillSwitchActivation:
        """
        Активирует Kill Switch.
        
        Args:
            trigger: Триггер активации
            reason: Причина активации
            target_mode: Целевой режим (SAFE или LOCKDOWN)
            activated_by: ID пользователя/системы
            metadata: Дополнительные метаданные
        
        Returns:
            KillSwitchActivation — информация об активации
        """
        previous_mode = self._status.current_mode
        
        # Проверяем, что переход допустим
        if not self._is_transition_allowed(previous_mode, target_mode):
            raise ValueError(
                f"Переход из {previous_mode} в {target_mode} недопустим. "
                f"Допустимые переходы: NORMAL -> SAFE, NORMAL -> LOCKDOWN, SAFE -> LOCKDOWN"
            )
        
        activation = KillSwitchActivation(
            trigger=trigger,
            reason=reason,
            previous_mode=previous_mode,
            new_mode=target_mode,
            activated_by=activated_by,
            metadata=metadata or {},
        )
        
        # Обновляем статус
        self._status.current_mode = target_mode
        self._status.is_active = target_mode != SystemMode.NORMAL
        self._status.last_activation = activation
        self._status.activation_history.append(activation)
        
        # Сохраняем статус
        self._save_status()
        
        # Логируем активацию (критическое событие)
        print(f"[KillSwitchManager] Kill Switch активирован: {activation.activation_id}")
        print(f"  Режим: {previous_mode} -> {target_mode}")
        print(f"  Триггер: {trigger.value}")
        print(f"  Причина: {reason}")
        
        return activation
    
    def deactivate(self, reason: str, deactivated_by: Optional[str] = None) -> KillSwitchActivation:
        """
        Деактивирует Kill Switch (возврат в NORMAL режим).
        
        Args:
            reason: Причина деактивации
            deactivated_by: ID пользователя/системы
        
        Returns:
            KillSwitchActivation — информация о деактивации
        """
        if self._status.current_mode == SystemMode.NORMAL:
            raise ValueError("Kill Switch уже деактивирован")
        
        previous_mode = self._status.current_mode
        
        activation = KillSwitchActivation(
            trigger=KillSwitchTrigger.MANUAL_ADMIN,
            reason=f"Деактивация: {reason}",
            previous_mode=previous_mode,
            new_mode=SystemMode.NORMAL,
            activated_by=deactivated_by,
        )
        
        # Обновляем статус
        self._status.current_mode = SystemMode.NORMAL
        self._status.is_active = False
        self._status.last_activation = activation
        self._status.activation_history.append(activation)
        
        # Сохраняем статус
        self._save_status()
        
        print(f"[KillSwitchManager] Kill Switch деактивирован: {activation.activation_id}")
        
        return activation
    
    def get_status(self) -> KillSwitchStatus:
        """Возвращает текущий статус Kill Switch."""
        return self._status
    
    def get_current_mode(self) -> SystemMode:
        """Возвращает текущий режим работы."""
        return self._status.current_mode
    
    def is_reasoning_enabled(self) -> bool:
        """Проверяет, включён ли reasoning."""
        return self._status.current_mode == SystemMode.NORMAL
    
    def get_safe_mode_limits(self) -> SafeModeLimits:
        """Возвращает ограничения для текущего режима."""
        mode = self._status.current_mode
        
        if mode == SystemMode.NORMAL:
            return SafeModeLimits(
                reasoning_enabled=True,
                new_decisions_allowed=True,
                evidence_access=True,
                audit_trail_access=True,
                last_decision_access=True,
            )
        elif mode == SystemMode.SAFE:
            return SafeModeLimits(
                reasoning_enabled=False,
                new_decisions_allowed=False,
                evidence_access=True,
                audit_trail_access=True,
                last_decision_access=True,
            )
        else:  # LOCKDOWN
            return SafeModeLimits(
                reasoning_enabled=False,
                new_decisions_allowed=False,
                evidence_access=False,
                audit_trail_access=True,
                last_decision_access=False,
            )
    
    def _is_transition_allowed(self, from_mode: SystemMode, to_mode: SystemMode) -> bool:
        """Проверяет, допустим ли переход между режимами."""
        # NORMAL -> SAFE или LOCKDOWN
        if from_mode == SystemMode.NORMAL:
            return to_mode in [SystemMode.SAFE, SystemMode.LOCKDOWN]
        
        # SAFE -> LOCKDOWN или NORMAL
        if from_mode == SystemMode.SAFE:
            return to_mode in [SystemMode.LOCKDOWN, SystemMode.NORMAL]
        
        # LOCKDOWN -> только NORMAL (через деактивацию)
        if from_mode == SystemMode.LOCKDOWN:
            return to_mode == SystemMode.NORMAL
        
        return False
    
    def check_guardrail_fail(self, guardrail_name: str, violation_details: str) -> bool:
        """
        Проверяет, нужно ли активировать Kill Switch при падении guardrail.
        
        Args:
            guardrail_name: Название guardrail
            violation_details: Детали нарушения
        
        Returns:
            True, если нужно активировать Kill Switch
        """
        # Критические guardrails требуют немедленной активации
        critical_guardrails = [
            'architecture_boundary',
            'decision_integrity',
            'red_team_replay',
        ]
        
        if guardrail_name in critical_guardrails:
            self.activate(
                trigger=KillSwitchTrigger.CI_GUARDRAIL_FAIL,
                reason=f"Критическое нарушение guardrail: {guardrail_name}. {violation_details}",
                target_mode=SystemMode.SAFE,
            )
            return True
        
        return False


# Глобальный экземпляр Kill Switch Manager
_kill_switch_manager: Optional[KillSwitchManager] = None


def get_kill_switch_manager() -> KillSwitchManager:
    """Возвращает глобальный экземпляр Kill Switch Manager."""
    global _kill_switch_manager
    if _kill_switch_manager is None:
        _kill_switch_manager = KillSwitchManager()
    return _kill_switch_manager

