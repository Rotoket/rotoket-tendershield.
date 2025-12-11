import React, { useState } from 'react';
import { Shield, Lock, ArrowRight, Loader2, AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react';
import { resetPassword } from '../services/authService';

interface ResetPasswordProps {
    token: string;
    onSuccess?: () => void;
}

const ResetPassword: React.FC<ResetPasswordProps> = ({ token, onSuccess }) => {
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!newPassword) {
            setError('Введите новый пароль');
            return;
        }

        if (newPassword.length < 6) {
            setError('Пароль должен содержать минимум 6 символов');
            return;
        }

        if (newPassword !== confirmPassword) {
            setError('Пароли не совпадают');
            return;
        }

        setIsLoading(true);

        try {
            await resetPassword(token, newPassword);
            setSuccess(true);
            
            // Вызываем callback если есть
            if (onSuccess) {
                setTimeout(() => {
                    onSuccess();
                }, 2000);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Произошла ошибка. Попробуйте снова.');
            console.error('[Reset Password Error]', err);
        } finally {
            setIsLoading(false);
        }
    };

    if (success) {
        return (
            <div className="min-h-screen bg-[#0f1419] flex items-center justify-center relative overflow-hidden">
                {/* Background Effects */}
                <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-[#00d4ff] opacity-5 blur-[120px] rounded-full"></div>
                <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-[#00e648] opacity-5 blur-[120px] rounded-full"></div>

                <div className="w-full max-w-md p-8 relative z-10">
                    <div className="text-center mb-10">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-[#1a1f2e] border border-[#2a3441] rounded-2xl mb-6 shadow-lg shadow-[#00e648]/10">
                            <CheckCircle className="text-[#00e648]" size={32} />
                        </div>
                        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Пароль изменён</h1>
                        <p className="text-[#a8b5cc]">Теперь вы можете войти с новым паролем</p>
                    </div>

                    <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-6 mb-6">
                        <p className="text-[#a8b5cc] text-sm text-center mb-4">
                            Пароль успешно изменён. Теперь вы можете войти в систему с новым паролем.
                        </p>
                    </div>

                    <button
                        onClick={() => {
                            // Удаляем токен из URL и перенаправляем на форму входа
                            window.history.replaceState({}, '', window.location.pathname);
                            if (onSuccess) {
                                onSuccess();
                            }
                        }}
                        className="w-full bg-gradient-to-r from-[#00d4ff] to-[#0099cc] text-[#0f1419] font-bold py-4 rounded-xl hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2"
                    >
                        Перейти к входу <ArrowRight size={20} />
                    </button>
                </div>
            </div>
        );
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
                    <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Новый пароль</h1>
                    <p className="text-[#a8b5cc]">Введите новый пароль для вашего аккаунта</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 flex items-start gap-3">
                            <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
                            <p className="text-red-400 text-sm">{error}</p>
                        </div>
                    )}

                    <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                            <Lock className="h-5 w-5 text-[#4b5563] group-focus-within:text-[#00d4ff] transition-colors" />
                        </div>
                        <input
                            type={showPassword ? 'text' : 'password'}
                            required
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            className="block w-full pl-11 pr-11 py-4 bg-[#1a1f2e] border border-[#2a3441] rounded-xl text-white placeholder-[#4b5563] focus:outline-none focus:border-[#00d4ff] focus:ring-1 focus:ring-[#00d4ff] transition-all"
                            placeholder="Новый пароль"
                            disabled={isLoading}
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

                    <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                            <Lock className="h-5 w-5 text-[#4b5563] group-focus-within:text-[#00d4ff] transition-colors" />
                        </div>
                        <input
                            type={showConfirmPassword ? 'text' : 'password'}
                            required
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="block w-full pl-11 pr-11 py-4 bg-[#1a1f2e] border border-[#2a3441] rounded-xl text-white placeholder-[#4b5563] focus:outline-none focus:border-[#00d4ff] focus:ring-1 focus:ring-[#00d4ff] transition-all"
                            placeholder="Подтвердите пароль"
                            disabled={isLoading}
                        />
                        <button
                            type="button"
                            onClick={() => setShowConfirmPassword((prev) => !prev)}
                            className="absolute inset-y-0 right-0 pr-4 flex items-center text-[#4b5563] hover:text-[#00d4ff] transition-colors"
                            aria-label={showConfirmPassword ? 'Скрыть пароль' : 'Показать пароль'}
                        >
                            {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                        </button>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-gradient-to-r from-[#00d4ff] to-[#0099cc] text-[#0f1419] font-bold py-4 rounded-xl hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed mt-6"
                    >
                        {isLoading ? (
                            <Loader2 className="animate-spin" size={20} />
                        ) : (
                            <>
                                Изменить пароль <ArrowRight size={20} />
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ResetPassword;

