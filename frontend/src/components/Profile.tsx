import React, { useState, useEffect } from 'react';
import { User } from '../types';
import { CreditCard, Users, Building2, Zap, FileText, Moon, Sun, Loader2, Star, ShieldCheck } from 'lucide-react';
import { getProfile, getTariffs, createPayment, updateCompanyProfile, type ProfileInfo, type TariffInfo, type UsageInfo, type PaymentInfo, type CompanyProfileInfo } from '../services/profileService';

interface ProfileProps {
    user: User | null;
}

const Profile: React.FC<ProfileProps> = ({ user }) => {
    const [isDark, setIsDark] = useState(true);
    const [profileData, setProfileData] = useState<ProfileInfo | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [tariffs, setTariffs] = useState<TariffInfo[]>([]);
    const [isCreatingPayment, setIsCreatingPayment] = useState(false);
    const [paymentError, setPaymentError] = useState<string | null>(null);
    const [isSavingCompanyProfile, setIsSavingCompanyProfile] = useState(false);
    const [orgForm, setOrgForm] = useState({
        name: user?.company || '',
        inn: '7701234567',
        kpp: '770101001',
        address: 'г. Москва, ул. Тверская, д. 1',
        director: 'Иванов Иван Иванович',
        email: user?.email || 'tender@vektor-ooo.ru'
    });

    const [companyProfile, setCompanyProfile] = useState<CompanyProfileInfo>({
        has_sro: false,
        has_fstek: false,
        has_fsb: false,
        has_mchs: false,
        experience_level: undefined,
        tax_system: undefined,
    });

    useEffect(() => {
        const loadProfile = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const [data, tariffsList] = await Promise.all([
                    getProfile(),
                    getTariffs(),
                ]);
                setProfileData(data);
                setTariffs(tariffsList);
                // Обновляем форму с данными пользователя
                setOrgForm(prev => ({
                    ...prev,
                    name: data.user.company || prev.name,
                    email: data.user.email || prev.email
                }));

                // Загружаем профиль компании, если есть
                if (data.company_profile) {
                    setCompanyProfile({
                        has_sro: data.company_profile.has_sro,
                        has_fstek: data.company_profile.has_fstek,
                        has_fsb: data.company_profile.has_fsb,
                        has_mchs: data.company_profile.has_mchs,
                        experience_level: data.company_profile.experience_level,
                        tax_system: data.company_profile.tax_system,
                    });
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Ошибка загрузки профиля');
                console.error('[Profile Error]', err);
            } finally {
                setIsLoading(false);
            }
        };

        if (user) {
            loadProfile();
        }
    }, [user]);

    const toggleTheme = () => {
        document.documentElement.classList.toggle('dark');
        setIsDark(!isDark);
    };

    const handleOrgChange = (field: string, value: string) => {
        setOrgForm(prev => ({ ...prev, [field]: value }));
    };

    const handleChangeTariff = async (tariff: TariffInfo) => {
        setPaymentError(null);
        setIsCreatingPayment(true);
        try {
            const payment: PaymentInfo = await createPayment(tariff.id);
            window.location.href = payment.confirmation_url;
        } catch (err) {
            console.error('[Payment Error]', err);
            setPaymentError(err instanceof Error ? err.message : 'Ошибка создания платежа');
        } finally {
            setIsCreatingPayment(false);
        }
    };

    const handleCompanyProfileChange = (field: keyof CompanyProfileInfo, value: boolean | string | undefined) => {
        setCompanyProfile(prev => ({ ...prev, [field]: value as any }));
    };

    const handleSaveCompanyProfile = async () => {
        if (!profileData) return;
        setIsSavingCompanyProfile(true);
        setError(null);
        try {
            const updated = await updateCompanyProfile(companyProfile);
            setProfileData(updated);
        } catch (err) {
            console.error('[CompanyProfile Error]', err);
            setError(err instanceof Error ? err.message : 'Не удалось сохранить профиль компании');
        } finally {
            setIsSavingCompanyProfile(false);
        }
    };

    return (
        <div className="animate-fade-in max-w-6xl mx-auto pb-10">
            <div className="flex justify-between items-start mb-8">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-2">Личный кабинет</h2>
                    <p className="text-slate-400">Управление организацией и настройками</p>
                </div>

                <button
                    onClick={toggleTheme}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#1a1f2e] border border-[#2a3441] text-white hover:border-[#00d4ff] transition-all shadow-sm"
                >
                    {isDark ? <Moon size={18} className="text-[#00d4ff]" /> : <Sun size={18} className="text-[#f59e0b]" />}
                    <span className="text-sm font-medium">{isDark ? 'Темная тема' : 'Светлая тема'}</span>
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Subscription & Usage */}
                <div className="space-y-6">
                    {/* Plan Card */}
                    <div className="bg-gradient-to-br from-[#1a1f2e] to-[#0f1419] border border-[#00d4ff]/30 rounded-2xl p-6 relative overflow-hidden shadow-lg shadow-[#00d4ff]/5">
                        <div className="absolute top-0 right-0 p-6 opacity-10">
                            <Zap size={120} className="text-[#00d4ff]" />
                        </div>
                        <div className="relative z-10">
                            {isLoading ? (
                                <div className="flex items-center justify-center py-8">
                                    <Loader2 className="animate-spin text-[#00d4ff]" size={24} />
                                </div>
                            ) : profileData?.tariff ? (
                                <>
                                    <span className="inline-block px-3 py-1 bg-[#00d4ff] text-[#0f1419] font-bold text-xs rounded-full mb-4">
                                        {profileData.tariff.name.toUpperCase()}
                                    </span>
                                    <h3 className="text-white text-lg font-bold">
                                        {profileData.tariff.name === 'Enterprise' ? 'Полный доступ' : `Тариф "${profileData.tariff.name}"`}
                                    </h3>
                                    <p className="text-slate-400 text-sm mb-6">
                                        {profileData.tariff.name === 'Enterprise'
                                            ? 'Все инструменты разблокированы'
                                            : `${profileData.tariff.analyses_limit === 0 ? '∞' : profileData.tariff.analyses_limit} анализов в месяц`}
                                    </p>

                                    <div className="text-3xl font-bold text-white mb-1">
                                        {profileData.tariff.price === 0 ? (
                                            <>Бесплатно</>
                                        ) : (
                                            <>{profileData.tariff.price.toLocaleString('ru-RU')} <span className="text-sm font-normal text-slate-400">₽/мес</span></>
                                        )}
                                    </div>
                                    {profileData.tariff.price > 0 && (
                                        <p className="text-xs text-slate-500 mb-6">Активная подписка</p>
                                    )}
                                </>
                            ) : (
                                <>
                                    <span className="inline-block px-3 py-1 bg-slate-600 text-white font-bold text-xs rounded-full mb-4">
                                        БЕЗ ТАРИФА
                                    </span>
                                    <h3 className="text-white text-lg font-bold">Тариф не выбран</h3>
                                    <p className="text-slate-400 text-sm mb-6">Выберите тариф для продолжения работы</p>
                                </>
                            )}

                            <button
                                className="w-full py-3 bg-[#0f1419] border border-[#2a3441] text-white rounded-xl font-medium hover:border-[#00d4ff] transition-colors disabled:opacity-60"
                                disabled={isCreatingPayment || tariffs.length === 0}
                                onClick={() => {
                                    const currentId = profileData?.tariff?.id;
                                    const currentPrice = profileData?.tariff?.price || 0;
                                    const target =
                                        tariffs.find(t => t.id !== currentId && t.price > currentPrice) ||
                                        tariffs.find(t => t.id !== currentId) ||
                                        tariffs[0];
                                    if (target) {
                                        handleChangeTariff(target);
                                    }
                                }}
                            >
                                {isCreatingPayment ? 'Создание платежа...' : 'Управление подпиской'}
                            </button>
                            {paymentError && (
                                <p className="mt-2 text-xs text-red-400">
                                    {paymentError}
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Usage Stats */}
                    <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6">
                        <h4 className="text-white font-bold mb-4 flex items-center gap-2">
                            <FileText size={18} className="text-[#00d4ff]" /> Статистика за месяц
                        </h4>

                        <div className="space-y-4">
                            {isLoading ? (
                                <div className="flex items-center justify-center py-4">
                                    <Loader2 className="animate-spin text-[#00d4ff]" size={20} />
                                </div>
                            ) : profileData?.usage ? (
                                <>
                                    <div>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="text-slate-400">AI Анализ</span>
                                            <span className="text-white font-bold">
                                                {profileData.usage.analyses_count}
                                                {profileData.usage.analyses_limit > 0 && ` / ${profileData.usage.analyses_limit}`}
                                                {profileData.usage.analyses_limit === 0 && ' / ∞'}
                                            </span>
                                        </div>
                                        {profileData.usage.analyses_limit > 0 ? (
                                            <>
                                                <div className="w-full h-2 bg-[#0f1419] rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full ${profileData.usage.analyses_remaining === 0
                                                            ? 'bg-red-500'
                                                            : profileData.usage.analyses_remaining <= profileData.usage.analyses_limit * 0.2
                                                                ? 'bg-yellow-500'
                                                                : 'bg-[#00d4ff]'
                                                            }`}
                                                        style={{
                                                            width: `${Math.min(100, (profileData.usage.analyses_count / profileData.usage.analyses_limit) * 100)}%`
                                                        }}
                                                    ></div>
                                                </div>
                                                {profileData.usage.analyses_remaining >= 0 && (
                                                    <p className="text-xs text-slate-500 mt-1">
                                                        Осталось: {profileData.usage.analyses_remaining} анализов
                                                    </p>
                                                )}
                                            </>
                                        ) : (
                                            <p className="text-xs text-slate-500 mt-1">Безлимитный тариф</p>
                                        )}
                                    </div>

                                    <div>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="text-slate-400">Пакетные анализы</span>
                                            <span className="text-white font-bold">
                                                {profileData.usage.packages_count}
                                                {profileData.usage.package_limit > 0 && ` / ${profileData.usage.package_limit}`}
                                                {profileData.usage.package_limit === 0 && ' / ∞'}
                                            </span>
                                        </div>
                                        {profileData.usage.package_limit > 0 ? (
                                            <>
                                                <div className="w-full h-2 bg-[#0f1419] rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full ${profileData.usage.packages_remaining === 0
                                                            ? 'bg-red-500'
                                                            : profileData.usage.packages_remaining <= profileData.usage.package_limit * 0.2
                                                                ? 'bg-yellow-500'
                                                                : 'bg-[#00e648]'
                                                            }`}
                                                        style={{
                                                            width: `${Math.min(100, (profileData.usage.packages_count / profileData.usage.package_limit) * 100)}%`
                                                        }}
                                                    ></div>
                                                </div>
                                                {profileData.usage.packages_remaining >= 0 && (
                                                    <p className="text-xs text-slate-500 mt-1">
                                                        Осталось: {profileData.usage.packages_remaining} пакетов
                                                    </p>
                                                )}
                                            </>
                                        ) : (
                                            <p className="text-xs text-slate-500 mt-1">Безлимитный тариф</p>
                                        )}
                                    </div>
                                </>
                            ) : error ? (
                                <div className="text-red-400 text-sm p-3 bg-red-500/10 border border-red-500/50 rounded-xl">
                                    {error}
                                </div>
                            ) : (
                                <p className="text-slate-500 text-sm">Нет данных об использовании</p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Middle Column: Company Info Form */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    <Building2 className="text-[#00d4ff]" /> Реквизиты организации
                                </h3>
                                <p className="text-slate-400 text-sm mt-1">Эти данные используются для автозаполнения документов и счетов.</p>
                            </div>
                            <button className="text-[#00d4ff] text-sm font-medium hover:underline bg-[#00d4ff]/10 px-3 py-1 rounded-lg">
                                Сохранить
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-1">
                                <label className="text-slate-500 text-xs font-bold uppercase">Название организации</label>
                                <input
                                    type="text"
                                    value={orgForm.name}
                                    onChange={(e) => handleOrgChange('name', e.target.value)}
                                    className="w-full bg-[#0f1419] border border-[#2a3441] p-3 rounded-xl text-white font-medium focus:border-[#00d4ff] outline-none"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-slate-500 text-xs font-bold uppercase">ИНН</label>
                                <input
                                    type="text"
                                    value={orgForm.inn}
                                    onChange={(e) => handleOrgChange('inn', e.target.value)}
                                    className="w-full bg-[#0f1419] border border-[#2a3441] p-3 rounded-xl text-white font-medium focus:border-[#00d4ff] outline-none"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-slate-500 text-xs font-bold uppercase">Электронная почта</label>
                                <input
                                    type="text"
                                    value={orgForm.email}
                                    onChange={(e) => handleOrgChange('email', e.target.value)}
                                    className="w-full bg-[#0f1419] border border-[#2a3441] p-3 rounded-xl text-white font-medium focus:border-[#00d4ff] outline-none"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Профиль компании для персонализации анализа */}
                    <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    <ShieldCheck className="text-[#00d4ff]" /> Профиль компании для анализа тендеров
                                </h3>
                                <p className="text-slate-400 text-sm mt-1">
                                    Отметьте, какие лицензии и опыт есть у вашей компании. Система будет подсвечивать только те барьеры, которых у вас нет.
                                </p>
                            </div>
                            <button
                                onClick={handleSaveCompanyProfile}
                                disabled={isSavingCompanyProfile}
                                className="text-[#00d4ff] text-sm font-medium hover:underline bg-[#00d4ff]/10 px-3 py-1 rounded-lg disabled:opacity-60"
                            >
                                {isSavingCompanyProfile ? 'Сохранение...' : 'Сохранить профиль'}
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <p className="text-slate-400 text-xs uppercase font-semibold">Лицензии и допуски</p>
                                <label className="flex items-center gap-2 text-sm text-slate-200">
                                    <input
                                        type="checkbox"
                                        checked={companyProfile.has_sro}
                                        onChange={(e) => handleCompanyProfileChange('has_sro', e.target.checked)}
                                        className="rounded border-[#2a3441] bg-[#0f1419] text-[#00d4ff]"
                                    />
                                    Есть СРО / допуски к строительным работам
                                </label>
                                <label className="flex items-center gap-2 text-sm text-slate-200">
                                    <input
                                        type="checkbox"
                                        checked={companyProfile.has_fstek}
                                        onChange={(e) => handleCompanyProfileChange('has_fstek', e.target.checked)}
                                        className="rounded border-[#2a3441] bg-[#0f1419] text-[#00d4ff]"
                                    />
                                    Есть лицензия ФСТЭК / защита информации
                                </label>
                                <label className="flex items-center gap-2 text-sm text-slate-200">
                                    <input
                                        type="checkbox"
                                        checked={companyProfile.has_fsb}
                                        onChange={(e) => handleCompanyProfileChange('has_fsb', e.target.checked)}
                                        className="rounded border-[#2a3441] bg-[#0f1419] text-[#00d4ff]"
                                    />
                                    Есть лицензия ФСБ
                                </label>
                                <label className="flex items-center gap-2 text-sm text-slate-200">
                                    <input
                                        type="checkbox"
                                        checked={companyProfile.has_mchs}
                                        onChange={(e) => handleCompanyProfileChange('has_mchs', e.target.checked)}
                                        className="rounded border-[#2a3441] bg-[#0f1419] text-[#00d4ff]"
                                    />
                                    Есть лицензия МЧС
                                </label>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-1">
                                    <p className="text-slate-400 text-xs uppercase font-semibold">Опыт участия</p>
                                    <select
                                        value={companyProfile.experience_level || ''}
                                        onChange={(e) =>
                                            handleCompanyProfileChange(
                                                'experience_level',
                                                e.target.value || undefined,
                                            )
                                        }
                                        className="w-full bg-[#0f1419] border border-[#2a3441] p-3 rounded-xl text-white text-sm focus:border-[#00d4ff] outline-none"
                                    >
                                        <option value="">Не указано</option>
                                        <option value="none">Только первые тендеры</option>
                                        <option value="up_to_10m">Опыт контрактов до 10 млн ₽</option>
                                        <option value="10_50m">Опыт контрактов 10–50 млн ₽</option>
                                        <option value="50m_plus">Опыт контрактов выше 50 млн ₽</option>
                                    </select>
                                </div>

                                <div className="space-y-1">
                                    <p className="text-slate-400 text-xs uppercase font-semibold">Система налогообложения</p>
                                    <select
                                        value={companyProfile.tax_system || ''}
                                        onChange={(e) =>
                                            handleCompanyProfileChange('tax_system', e.target.value || undefined)
                                        }
                                        className="w-full bg-[#0f1419] border border-[#2a3441] p-3 rounded-xl text-white text-sm focus:border-[#00d4ff] outline-none"
                                    >
                                        <option value="">Не указано</option>
                                        <option value="OSN">ОСН</option>
                                        <option value="USN">УСН</option>
                                        <option value="PATENT">Патент</option>
                                    </select>
                                </div>

                                <p className="text-[11px] text-slate-500">
                                    Профиль компании используется только для расчёта рисков и не передаётся в документы.
                                    Это помогает системе отличать реальные барьеры от тех, которые для вас уже закрыты.
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6">
                            <h4 className="text-white font-bold mb-4 flex items-center gap-2">
                                <Users size={18} className="text-[#00d4ff]" /> Доступ сотрудников
                            </h4>
                            <div className="space-y-3">
                                <div className="flex items-center justify-between p-3 bg-[#0f1419] rounded-xl border border-[#2a3441]">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-[#2a3441] flex items-center justify-center text-white text-xs font-bold">И</div>
                                        <div>
                                            <p className="text-white text-sm font-medium">Иван И.</p>
                                            <p className="text-slate-500 text-xs">Администратор</p>
                                        </div>
                                    </div>
                                    <span className="w-2 h-2 bg-[#00e648] rounded-full"></span>
                                </div>
                            </div>
                            <button className="w-full mt-4 py-2 border border-dashed border-[#2a3441] text-slate-500 rounded-xl text-sm hover:text-white hover:border-[#00d4ff] transition-colors">
                                + Добавить сотрудника
                            </button>
                        </div>

                        <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6">
                            <h4 className="text-white font-bold mb-4 flex items-center gap-2">
                                <CreditCard size={18} className="text-[#00d4ff]" /> Платежные данные
                            </h4>
                            <div className="p-4 bg-[#0f1419] border border-[#2a3441] rounded-xl mb-4 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-6 bg-[#2a3441] rounded flex items-center justify-center text-[10px] text-white font-bold">MIR</div>
                                    <span className="text-white font-mono text-sm">•••• 4582</span>
                                </div>
                                <span className="text-[#00e648] text-xs font-bold bg-[#00e648]/10 px-2 py-1 rounded">ОСНОВНОЙ</span>
                            </div>
                            <div className="flex flex-col gap-3">
                                <button className="text-[#00d4ff] text-sm font-medium hover:underline text-left">
                                    Скачать закрывающие документы
                                </button>
                                {tariffs.length > 0 && (
                                    <div className="mt-2 border-t border-[#2a3441] pt-3">
                                        <p className="text-xs text-slate-500 mb-2 flex items-center gap-1">
                                            <Star size={12} className="text-[#00d4ff]" /> Доступные тарифы
                                        </p>
                                        <div className="flex flex-wrap gap-2">
                                            {tariffs.map(t => (
                                                <button
                                                    key={t.id}
                                                    onClick={() => handleChangeTariff(t)}
                                                    disabled={isCreatingPayment}
                                                    className="px-3 py-1 rounded-full border border-[#2a3441] text-xs text-slate-200 hover:border-[#00d4ff] hover:text-white disabled:opacity-60"
                                                >
                                                    {t.name} · {t.price === 0 ? 'Бесплатно' : `${t.price.toLocaleString('ru-RU')} ₽/мес`}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;