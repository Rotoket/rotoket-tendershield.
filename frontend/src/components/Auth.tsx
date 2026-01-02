import React, { useState } from 'react';
import { Shield, Lock, Mail, ArrowRight, Loader2, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { User } from '../types';
import { login, register, type AuthUser } from '../services/authService';
import ForgotPassword from './ForgotPassword';

interface AuthProps {
    onLogin: (user: User) => void;
    /** Причина авторизации (для позиционирования) */
    reason?: 'fix_decision' | 'general';
}

const Auth: React.FC<AuthProps> = ({ onLogin, reason = 'general' }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [isRegisterMode, setIsRegisterMode] = useState(false);
    const [showForgotPassword, setShowForgotPassword] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [company, setCompany] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [agreeTerms, setAgreeTerms] = useState(false);
    const [agreePdn, setAgreePdn] = useState(false);
    const [activeDoc, setActiveDoc] = useState<null | 'terms' | 'pdn'>(null);
    const [showPassword, setShowPassword] = useState(false);

    const mapAuthUserToUser = (authUser: AuthUser): User => {
        const tariffMap: ('Start' | 'Pro' | 'Enterprise')[] = ['Start', 'Pro', 'Enterprise'];
        const tariff: 'Start' | 'Pro' | 'Enterprise' = authUser.tariff_id && authUser.tariff_id >= 1 && authUser.tariff_id <= 3
            ? tariffMap[authUser.tariff_id - 1]
            : 'Start';

        // Безопасная обработка email (может быть undefined в fallback случае)
        const email = authUser.email || '';
        const emailName = email.split('@')[0] || 'Специалист';

        return {
            id: (authUser.id !== undefined && authUser.id !== null) ? authUser.id.toString() : '0',
            name: authUser.name || emailName,
            company: authUser.company || 'Организация',
            tariff,
            email: email || '',
        };
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!agreeTerms || !agreePdn) {
            setError('Необходимо принять условия пользовательского соглашения и политику обработки ПДн');
            return;
        }

        if (!email || !password) {
            setError('Заполните все обязательные поля');
            return;
        }

        if (isRegisterMode && !name) {
            setError('Укажите ваше имя');
            return;
        }

        setIsLoading(true);

        try {
            let authUser: AuthUser;

            if (isRegisterMode) {
                // Регистрация
                authUser = await register({
                    email,
                    password,
                    name: name || undefined,
                    company: company || undefined,
                });
                // После регистрации автоматически входим
                const loginResponse = await login({ email, password });
                authUser = loginResponse.user;
            } else {
                // Вход
                const loginResponse = await login({ email, password });
                authUser = loginResponse.user;
            }

            // Преобразуем AuthUser в User и вызываем onLogin
            onLogin(mapAuthUserToUser(authUser));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Произошла ошибка. Попробуйте снова.');
            console.error('[Auth Error]', err);
        } finally {
            setIsLoading(false);
        }
    };

    if (showForgotPassword) {
        return <ForgotPassword onBack={() => setShowForgotPassword(false)} />;
    }

    return (
        <div className="min-h-screen bg-[#0f1419] flex items-center justify-center relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-[#00d4ff] opacity-5 blur-[120px] rounded-full"></div>
            <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-[#00e648] opacity-5 blur-[120px] rounded-full"></div>

            <div className="w-full max-w-md p-8 relative z-10">
                <div className="text-center mb-10">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-[#1a1f2e] border border-[#2a3441] rounded-2xl mb-6 shadow-lg shadow-[#00d4ff]/10">
                        <Shield className="text-[#00d4ff]" size={32} />
                    </div>
                    {reason === 'fix_decision' ? (
                        <>
                            <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">
                                Подтверждение доступа для фиксации решения
                            </h1>
                            <p className="text-[#a8b5cc] text-sm leading-relaxed">
                                Решение по тендеру фиксируется за конкретным лицом.
                                Это требуется для отчётов, аудита и защиты репутации.
                            </p>
                        </>
                    ) : (
                        <>
                            <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Тендер.Щит</h1>
                            <p className="text-[#a8b5cc]">Система управленческих решений по тендерам</p>
                        </>
                    )}
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 flex items-start gap-3">
                            <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
                            <p className="text-red-400 text-sm">{error}</p>
                        </div>
                    )}

                    {isRegisterMode && (
                        <div className="relative group">
                            <input
                                type="text"
                                required
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="block w-full pl-4 pr-4 py-4 bg-[#1a1f2e] border border-[#2a3441] rounded-xl text-white placeholder-[#4b5563] focus:outline-none focus:border-[#00d4ff] focus:ring-1 focus:ring-[#00d4ff] transition-all"
                                placeholder="Ваше имя"
                            />
                        </div>
                    )}

                    {isRegisterMode && (
                        <div className="relative group">
                            <input
                                type="text"
                                value={company}
                                onChange={(e) => setCompany(e.target.value)}
                                className="block w-full pl-4 pr-4 py-4 bg-[#1a1f2e] border border-[#2a3441] rounded-xl text-white placeholder-[#4b5563] focus:outline-none focus:border-[#00d4ff] focus:ring-1 focus:ring-[#00d4ff] transition-all"
                                placeholder="Название организации (необязательно)"
                            />
                        </div>
                    )}

                    <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                            <Mail className="h-5 w-5 text-[#4b5563] group-focus-within:text-[#00d4ff] transition-colors" />
                        </div>
                        <input
                            type="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="block w-full pl-11 pr-4 py-4 bg-[#1a1f2e] border border-[#2a3441] rounded-xl text-white placeholder-[#4b5563] focus:outline-none focus:border-[#00d4ff] focus:ring-1 focus:ring-[#00d4ff] transition-all"
                            placeholder="Рабочая почта"
                        />
                    </div>

                    <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                            <Lock className="h-5 w-5 text-[#4b5563] group-focus-within:text-[#00d4ff] transition-colors" />
                        </div>
                        <input
                            type={showPassword ? 'text' : 'password'}
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="block w-full pl-11 pr-11 py-4 bg-[#1a1f2e] border border-[#2a3441] rounded-xl text-white placeholder-[#4b5563] focus:outline-none focus:border-[#00d4ff] focus:ring-1 focus:ring-[#00d4ff] transition-all"
                            placeholder="Пароль доступа"
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword((prev) => !prev)}
                            className="absolute inset-y-0 right-0 pr-4 flex items-center text-[#4b5563] hover:text-[#00d4ff] transition-colors"
                            aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
                        >
                            {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                        </button>
                    </div>

                    {!isRegisterMode && (
                        <div className="text-right">
                            <button
                                type="button"
                                onClick={() => setShowForgotPassword(true)}
                                className="text-[#4b5563] text-sm hover:text-[#00d4ff] transition-colors"
                            >
                                Забыли пароль?
                            </button>
                        </div>
                    )}

                    <div className="space-y-2 text-xs text-[#a8b5cc] mt-2">
                        <label className="flex items-start gap-2">
                            <input
                                type="checkbox"
                                checked={agreeTerms}
                                onChange={(e) => setAgreeTerms(e.target.checked)}
                                className="mt-0.5 h-3 w-3 rounded border-[#2a3441] bg-[#0f1419] text-[#00d4ff] focus:ring-[#00d4ff]"
                            />
                            <span>
                                Я принимаю условия{' '}
                                <button
                                    type="button"
                                    onClick={() => setActiveDoc('terms')}
                                    className="text-[#00d4ff] underline underline-offset-2 decoration-dotted hover:text-[#33e0ff]"
                                >
                                    пользовательского соглашения
                                </button>{' '}
                                и понимаю, что сервис фиксирует аналитическую оценку и не является юридической консультацией.
                            </span>
                        </label>
                        <label className="flex items-start gap-2">
                            <input
                                type="checkbox"
                                checked={agreePdn}
                                onChange={(e) => setAgreePdn(e.target.checked)}
                                className="mt-0.5 h-3 w-3 rounded border-[#2a3441] bg-[#0f1419] text-[#00d4ff] focus:ring-[#00d4ff]"
                            />
                            <span>
                                Я подтверждаю законность загрузки документов и даю согласие на обработку возможных персональных данных в системе в соответствии с{' '}
                                <button
                                    type="button"
                                    onClick={() => setActiveDoc('pdn')}
                                    className="text-[#00d4ff] underline underline-offset-2 decoration-dotted hover:text-[#33e0ff]"
                                >
                                    152-ФЗ и Политикой обработки ПДн
                                </button>
                                .
                            </span>
                        </label>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading || !agreeTerms || !agreePdn}
                        className="w-full bg-gradient-to-r from-[#00d4ff] to-[#0099cc] text-[#0f1419] font-bold py-4 rounded-xl hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed mt-6"
                    >
                        {isLoading ? (
                            <Loader2 className="animate-spin" size={20} />
                        ) : (
                            <>
                                {isRegisterMode ? 'Зарегистрироваться' : 'Войти в систему'} <ArrowRight size={20} />
                            </>
                        )}
                    </button>
                </form>

                <div className="mt-8 text-center">
                    <p className="text-[#4b5563] text-sm">
                        {isRegisterMode ? (
                            <>
                                Уже есть аккаунт?{' '}
                                <button
                                    onClick={() => {
                                        setIsRegisterMode(false);
                                        setError(null);
                                    }}
                                    className="text-[#00d4ff] hover:underline"
                                >
                                    Войти
                                </button>
                            </>
                        ) : (
                            <>
                                Нет аккаунта?{' '}
                                <button
                                    onClick={() => {
                                        setIsRegisterMode(true);
                                        setError(null);
                                    }}
                                    className="text-[#00d4ff] hover:underline"
                                >
                                    Зарегистрироваться
                                </button>
                            </>
                        )}
                    </p>
                </div>
            </div>

            {activeDoc && (
                <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/60">
                    <div className="max-w-2xl w-full mx-4 bg-[#0f1419] border border-[#2a3441] rounded-2xl p-6 relative">
                        <button
                            type="button"
                            onClick={() => setActiveDoc(null)}
                            className="absolute top-3 right-3 text-slate-400 hover:text-white text-sm"
                        >
                            ✕
                        </button>
                        <h2 className="text-xl font-bold text-white mb-3">
                            {activeDoc === 'terms' ? 'Пользовательское соглашение' : 'Политика обработки персональных данных'}
                        </h2>
                        <div className="text-xs text-[#a8b5cc] space-y-2 max-h-[60vh] overflow-y-auto pr-2">
                            {activeDoc === 'terms' ? (
                                <>
                                    <p>
                                        Сервис «Тендер.Щит» предоставляет пользователю инструменты аналитической оценки тендерной документации. Сервис не является юридической консультацией и не гарантирует исход закупочных процедур.
                                    </p>
                                    <p>
                                        Пользователь обязуется использовать сервис только при наличии законных оснований для обработки документов, полученных от заказчиков и партнёров, и самостоятельно несёт ответственность за содержание загружаемых файлов.
                                    </p>
                                    <p>
                                        Все решения об участии в закупках, подаче жалоб, подготовке заявок и иных действиях принимает пользователь либо его уполномоченный специалист. Результаты анализа носят предварительный характер и требуют проверки специалистом.
                                    </p>
                                    <p>
                                        Администратор сервиса оставляет за собой право изменять функционал и правила работы сервиса, публикуя обновлённую редакцию соглашения. Продолжение использования сервиса означает согласие с актуальными условиями.
                                    </p>
                                </>
                            ) : (
                                <>
                                    <p>
                                        Персональные данные могут обрабатываться в составе загружаемой пользователем тендерной документации (ФИО, контакты ответственных лиц, идентификаторы и т.п.). Обработка таких данных осуществляется исключительно в целях оказания услуг по аналитике тендерной документации пользователю сервиса.
                                    </p>
                                    <p>
                                        Пользователь гарантирует, что обладает всеми необходимыми правами и согласиями для передачи документов в систему, и несёт ответственность за законность получения и использования персональных данных третьих лиц.
                                    </p>
                                    <p>
                                        Администратор сервиса принимает разумные организационные и технические меры для защиты загруженных документов: ограничение доступа по аккаунтам, регистрация действий, использование защищённых каналов связи. Режим хранения и срок обработки определяются договорённостями с пользователем.
                                    </p>
                                    <p>
                                        Пользователь вправе запросить удаление своих данных и прекращение обработки персональных данных в пределах, допускаемых законодательством РФ о ПДн.
                                    </p>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Auth;