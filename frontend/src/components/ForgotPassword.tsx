import React, { useState } from 'react';
import { Shield, Mail, ArrowRight, Loader2, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react';
import { forgotPassword } from '../services/authService';

interface ForgotPasswordProps {
    onBack: () => void;
}

const ForgotPassword: React.FC<ForgotPasswordProps> = ({ onBack }) => {
    const [email, setEmail] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccess(false);

        if (!email) {
            setError('Введите email');
            return;
        }

        setIsLoading(true);

        try {
            await forgotPassword(email);
            setSuccess(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Произошла ошибка. Попробуйте снова.');
            console.error('[Forgot Password Error]', err);
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
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-[#1a1f2e] border border-[#2a3441] rounded-2xl mb-6 shadow-lg shadow-[#00d4ff]/10">
                            <CheckCircle className="text-[#00e648]" size={32} />
                        </div>
                        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Письмо отправлено</h1>
                        <p className="text-[#a8b5cc]">Проверьте вашу почту</p>
                    </div>

                    <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-6 mb-6">
                        <p className="text-[#a8b5cc] text-sm mb-4">
                            Если указанный email зарегистрирован в системе, на него будет отправлена инструкция по сбросу пароля.
                        </p>
                        <p className="text-[#a8b5cc] text-sm">
                            Ссылка для сброса пароля действительна в течение <strong className="text-white">1 часа</strong>.
                        </p>
                    </div>

                    <button
                        onClick={onBack}
                        className="w-full bg-[#1a1f2e] border border-[#2a3441] text-white font-medium py-4 rounded-xl hover:bg-[#2a3441] transition-all flex items-center justify-center gap-2"
                    >
                        <ArrowLeft size={20} /> Вернуться к входу
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
                    <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Восстановление пароля</h1>
                    <p className="text-[#a8b5cc]">Введите email для получения ссылки сброса</p>
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
                            <Mail className="h-5 w-5 text-[#4b5563] group-focus-within:text-[#00d4ff] transition-colors" />
                        </div>
                        <input
                            type="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="block w-full pl-11 pr-4 py-4 bg-[#1a1f2e] border border-[#2a3441] rounded-xl text-white placeholder-[#4b5563] focus:outline-none focus:border-[#00d4ff] focus:ring-1 focus:ring-[#00d4ff] transition-all"
                            placeholder="Рабочая почта"
                            disabled={isLoading}
                        />
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
                                Отправить ссылку <ArrowRight size={20} />
                            </>
                        )}
                    </button>
                </form>

                <div className="mt-8 text-center">
                    <button
                        onClick={onBack}
                        className="text-[#4b5563] text-sm hover:text-[#00d4ff] transition-colors flex items-center justify-center gap-2 mx-auto"
                    >
                        <ArrowLeft size={16} /> Вернуться к входу
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ForgotPassword;







