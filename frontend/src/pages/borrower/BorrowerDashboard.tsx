import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/context/AuthContext';
import {
    authService,
    CreditInfo,
    ShapExplanation,
    LimeExplanation,
    GeminiAdvice,
} from '@/services/authService';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { ShieldCheck, TrendingUp, Wallet, AlertTriangle, CheckCircle, Info, Sparkles, Target, Lightbulb, DollarSign, Percent, TrendingDown, Clock, Users, ArrowRight, Zap } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

const riskConfig: Record<string, { color: string; icon: typeof ShieldCheck; label: string }> = {
    low: { color: 'bg-green-100 text-green-800 border-green-200', icon: CheckCircle, label: 'Low Risk' },
    medium: { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: AlertTriangle, label: 'Medium Risk' },
    high: { color: 'bg-red-100 text-red-800 border-red-200', icon: AlertTriangle, label: 'High Risk' },
};

const normalizeRuleText = (text: string) => text.replace(/_/g, ' ').replace(/\s+/g, ' ').trim();

const extractFeatureFromRule = (rawRule: string) => {
    const cleanedRule = normalizeRuleText(rawRule);
    const match = cleanedRule.match(/^(.*?)(<=|>=|<|>|=)\s*(-?\d+(?:\.\d+)?)$/);
    if (!match) return cleanedRule.toLowerCase();
    return normalizeRuleText(match[1]).toLowerCase();
};

const extractRuleOperator = (rawRule: string) => {
    const cleanedRule = normalizeRuleText(rawRule);
    const match = cleanedRule.match(/^(.*?)(<=|>=|<|>|=)\s*(-?\d+(?:\.\d+)?)$/);
    return match?.[2] ?? null;
};

const getDisplayLimeEffect = (rawRule: string, fallback: 'helps' | 'hurts') => {
    const feature = extractFeatureFromRule(rawRule);
    const operator = extractRuleOperator(rawRule);

    if (!operator) return fallback;

    const trend = operator === '<=' || operator === '<' ? 'lower' : operator === '>=' || operator === '>' ? 'higher' : 'neutral';
    if (trend === 'neutral') return fallback;

    const lowerIsBetterFeatures = [
        'number of existing loans',
        'existing loans',
        'loan count',
        'debt to income ratio',
        'dti',
        'utilization',
        'late payment',
        'overdue',
    ];

    const higherIsBetterFeatures = [
        'credit history length',
        'income',
        'monthly income',
        'savings',
        'payment history',
    ];

    const lowerIsBetter = lowerIsBetterFeatures.some((token) => feature.includes(token));
    const higherIsBetter = higherIsBetterFeatures.some((token) => feature.includes(token));

    if (lowerIsBetter) return trend === 'lower' ? 'helps' : 'hurts';
    if (higherIsBetter) return trend === 'higher' ? 'helps' : 'hurts';

    return fallback;
};

const isUsefulLimeRule = (rule: { rule: string; impact: number }, readableRule: string) => {
    const feature = extractFeatureFromRule(rule.rule);
    const nonActionableFeatures = ['city', 'existing customer', 'customer id', 'user id', 'id'];
    const hasNonActionableFeature = nonActionableFeatures.some((token) => feature.includes(token));
    const hasVagueText = readableRule.toLowerCase().includes('around this level');
    const hasMeaningfulImpact = Math.abs(rule.impact) >= 1;

    return !hasNonActionableFeature && !hasVagueText && hasMeaningfulImpact;
};

const toReadableLimeRule = (rawRule: string) => {
    const cleanedRule = normalizeRuleText(rawRule);
    const match = cleanedRule.match(/^(.*?)(<=|>=|<|>|=)\s*(-?\d+(?:\.\d+)?)$/);

    if (!match) return cleanedRule;

    const [, rawFeature, operator, rawValue] = match;
    const feature = normalizeRuleText(rawFeature);
    const numericValue = Number(rawValue);
    const hasModelScaledValue = Number.isFinite(numericValue) && (!Number.isInteger(numericValue) || numericValue < 0);

    if (hasModelScaledValue) {
        if (operator === '<=' || operator === '<') return `${feature} is on the lower side`;
        if (operator === '>=' || operator === '>') return `${feature} is on the higher side`;
        return `${feature} is around this level`;
    }

    const value = Number.isFinite(numericValue) ? numericValue.toString() : rawValue;

    if (operator === '<=') return `${feature} is ${value} or below`;
    if (operator === '>=') return `${feature} is ${value} or above`;
    if (operator === '<') return `${feature} is below ${value}`;
    if (operator === '>') return `${feature} is above ${value}`;
    return `${feature} is ${value}`;
};

const toReadableLimeSummary = (ruleText: string, effect: 'helps' | 'hurts') => {
    return `${ruleText} ${effect === 'helps' ? 'helps' : 'hurts'} your credit score.`;
};

const BorrowerDashboard = () => {
    const { user } = useAuth();
    const [creditInfo, setCreditInfo] = useState<CreditInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [shapExplanation, setShapExplanation] = useState<ShapExplanation | null>(null);
    const [limeExplanation, setLimeExplanation] = useState<LimeExplanation | null>(null);
    const [geminiAdvice, setGeminiAdvice] = useState<GeminiAdvice | null>(null);
    const [explanationLoading, setExplanationLoading] = useState(true);
    const [explanationErrors, setExplanationErrors] = useState<string[]>([]);

    // Helper to get icon and explanation for factors
    const getFactorIcon = (feature: string) => {
        const lower = feature.toLowerCase();
        if (lower.includes('loan')) return DollarSign;
        if (lower.includes('income')) return Wallet;
        if (lower.includes('payment') || lower.includes('time')) return Clock;
        if (lower.includes('age') || lower.includes('tenure')) return Users;
        if (lower.includes('ratio')) return Percent;
        return TrendingUp;
    };

    // Calculate max impact for normalization
    const getMaxImpact = (factors: any[]) => {
        return Math.max(1, ...factors.map(f => Math.abs(f.impact)));
    };

    useEffect(() => {
        const fetchCreditInfo = async () => {
            if (!user?.id) return;
            try {
                const data = await authService.getCreditInfo(user.id);
                setCreditInfo(data);
            } catch {
                setError('Failed to load credit information.');
            } finally {
                setLoading(false);
            }
        };

        const fetchExplanations = async () => {
            if (!user?.id) return;
            setExplanationLoading(true);

            const [shapResult, limeResult, adviceResult] = await Promise.allSettled([
                authService.getShapExplanation(user.id),
                authService.getLimeExplanation(user.id),
                authService.getGeminiAdvice(user.id),
            ]);

            const errors: string[] = [];

            if (shapResult.status === 'fulfilled') {
                setShapExplanation(shapResult.value);
            } else {
                errors.push('SHAP explanation unavailable right now.');
            }

            if (limeResult.status === 'fulfilled') {
                setLimeExplanation(limeResult.value);
            } else {
                errors.push('LIME explanation unavailable right now.');
            }

            if (adviceResult.status === 'fulfilled') {
                setGeminiAdvice(adviceResult.value);
            } else {
                errors.push('Advice generation unavailable right now.');
            }

            setExplanationErrors(errors);
            setExplanationLoading(false);
        };

        fetchCreditInfo();
        fetchExplanations();
    }, [user?.id]);

    const riskKey = creditInfo?.Risk?.toLowerCase() ?? 'low';
    const risk = riskConfig[riskKey] ?? riskConfig.low;
    const RiskIcon = risk.icon;

    // Credit score color
    const scoreColor = (score: number) => {
        if (score >= 750) return 'text-green-600';
        if (score >= 600) return 'text-yellow-600';
        return 'text-red-600';
    };

    return (
        <div className="flex-1 space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
            </div>

            {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                    {error}
                </div>
            )}

            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-3">
                {/* Credit Score */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Credit Score</CardTitle>
                        <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <Skeleton className="h-10 w-24" />
                        ) : (
                            <>
                                <div className={`text-4xl font-bold ${scoreColor(creditInfo?.creditScore ?? 0)}`}>
                                    {creditInfo?.creditScore ?? '—'}
                                </div>
                                <p className="text-xs text-muted-foreground mt-1">Out of 900</p>
                            </>
                        )}
                    </CardContent>
                </Card>

                {/* Risk Level */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Risk Level</CardTitle>
                        <ShieldCheck className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <Skeleton className="h-10 w-32" />
                        ) : (
                            <div className="flex items-center gap-2 mt-1">
                                <RiskIcon className="h-6 w-6" />
                                <Badge variant="outline" className={`text-base px-3 py-1 ${risk.color}`}>
                                    {risk.label}
                                </Badge>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Estimated Credit Line */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Estimated Credit Line</CardTitle>
                        <Wallet className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <Skeleton className="h-10 w-28" />
                        ) : (
                            <>
                                <div className="text-4xl font-bold">
                                    ₹{(creditInfo?.creditLine ?? 0).toLocaleString('en-IN')}
                                </div>
                                <p className="text-xs text-muted-foreground mt-1">Maximum eligible amount</p>
                            </>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Explanations */}
            <Card>
                <CardHeader className="flex flex-row items-center gap-2">
                    <Info className="h-5 w-5 text-primary" />
                    <CardTitle>What does this mean?</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-sm text-muted-foreground">
                    <div>
                        <span className="font-semibold text-foreground">Credit Score</span> — A numerical representation of your creditworthiness based on
                        your financial history, employment, and existing obligations. Scores above 750 are excellent.
                    </div>
                    <div>
                        <span className="font-semibold text-foreground">Risk Level</span> — Indicates how risky a lender may consider your profile.
                        <span className="text-green-600 font-medium"> Low</span> means highly trustworthy,
                        <span className="text-yellow-600 font-medium"> Medium</span> means average risk, and
                        <span className="text-red-600 font-medium"> High</span> means the profile needs improvement.
                    </div>
                    <div>
                        <span className="font-semibold text-foreground">Estimated Credit Line</span> — The approximate maximum loan amount you can be eligible for,
                        based on your credit score, income, and existing financial commitments.
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center gap-2">
                    <Sparkles className="h-5 w-5 text-primary" />
                    <CardTitle>Score Explanations And Improvement Advice</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {explanationLoading ? (
                        <div className="space-y-3">
                            <Skeleton className="h-10 w-full" />
                            <Skeleton className="h-24 w-full" />
                            <Skeleton className="h-24 w-full" />
                        </div>
                    ) : (
                        <>
                            {explanationErrors.length > 0 && (
                                <Alert variant="default" className="border-yellow-300 bg-yellow-50 text-yellow-900">
                                    <AlertTitle>Some explanation sections are unavailable</AlertTitle>
                                    <AlertDescription>
                                        {explanationErrors.join(' ')}
                                    </AlertDescription>
                                </Alert>
                            )}

                            <Tabs defaultValue="shap" className="w-full">
                                <TabsList className="grid w-full grid-cols-3">
                                    <TabsTrigger value="shap">SHAP Factors</TabsTrigger>
                                    <TabsTrigger value="lime">LIME Rules</TabsTrigger>
                                    <TabsTrigger value="advice">Advice</TabsTrigger>
                                </TabsList>

                                <TabsContent value="shap" className="space-y-3">
                                    {shapExplanation?.topFactors?.length ? (
                                        <>
                                            <div className="text-xs text-muted-foreground bg-blue-50 border border-blue-200 rounded-lg p-3 mb-2">
                                                <p><strong>What you're seeing:</strong> These are key factors from your financial profile that most impact your credit score.</p>
                                            </div>
                                            {(() => {
                                                const maxImpact = getMaxImpact(shapExplanation.topFactors);
                                                return shapExplanation.topFactors.map((factor, index) => {
                                                    const IconComponent = getFactorIcon(factor.feature);
                                                    const impactPercent = (Math.abs(factor.impact) / maxImpact) * 100;
                                                    const isNegative = factor.direction === 'hurts';
                                                    
                                                    return (
                                                        <div
                                                            key={`${factor.feature}-${index}`}
                                                            className={`rounded-lg border p-4 transition-all hover:shadow-md ${
                                                                isNegative 
                                                                    ? 'border-red-200 bg-red-50' 
                                                                    : 'border-green-200 bg-green-50'
                                                            }`}
                                                        >
                                                            <div className="flex gap-4">
                                                                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                                                                    isNegative ? 'bg-red-200' : 'bg-green-200'
                                                                }`}>
                                                                    <IconComponent className={`w-5 h-5 ${isNegative ? 'text-red-700' : 'text-green-700'}`} />
                                                                </div>
                                                                <div className="flex-grow">
                                                                    <div className="flex items-start justify-between mb-2">
                                                                        <h4 className={`font-semibold ${isNegative ? 'text-red-900' : 'text-green-900'}`}>
                                                                            {factor.feature}
                                                                        </h4>
                                                                        <Badge className={isNegative ? 'bg-red-600' : 'bg-green-600'}>
                                                                            {factor.direction === 'helps' ? '↑ Helps' : '↓ Hurts'}
                                                                        </Badge>
                                                                    </div>
                                                                    <p className={`text-sm mb-3 ${isNegative ? 'text-red-800' : 'text-green-800'}`}>
                                                                        {factor.summary}
                                                                    </p>
                                                                    <div className="space-y-2">
                                                                        <div className="flex justify-between items-center text-xs">
                                                                            <span className={`font-medium ${isNegative ? 'text-red-700' : 'text-green-700'}`}>
                                                                                Impact strength
                                                                            </span>
                                                                            <span className={`font-bold text-sm ${isNegative ? 'text-red-700' : 'text-green-700'}`}>
                                                                                {Math.abs(factor.impact).toFixed(1)} pts
                                                                            </span>
                                                                        </div>
                                                                        <div className={`w-full h-2 rounded-full overflow-hidden ${isNegative ? 'bg-red-200' : 'bg-green-200'}`}>
                                                                            <div 
                                                                                className={`h-full ${isNegative ? 'bg-red-600' : 'bg-green-600'}`}
                                                                                style={{ width: `${impactPercent}%` }}
                                                                            />
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    );
                                                });
                                            })()}
                                        </>
                                    ) : (
                                        <p className="text-sm text-muted-foreground">SHAP factor details are not available right now.</p>
                                    )}
                                </TabsContent>

                                <TabsContent value="lime" className="space-y-3">
                                    {limeExplanation?.rules?.length ? (
                                        <>
                                            <div className="text-xs text-muted-foreground bg-purple-50 border border-purple-200 rounded-lg p-3 mb-2">
                                                <p><strong>What you're seeing:</strong> These are the most useful and actionable conditions from your profile that explain your score.</p>
                                            </div>
                                            {(() => {
                                                const preparedRules = limeExplanation.rules
                                                    .map((rule) => {
                                                        const displayEffect = rule.effect;
                                                        const readableRule = toReadableLimeRule(rule.rule);
                                                        const backendSummary = (rule.summary || '').trim();
                                                        const readableSummary = backendSummary || toReadableLimeSummary(readableRule, displayEffect);
                                                        return {
                                                            ...rule,
                                                            displayEffect,
                                                            readableRule,
                                                            readableSummary,
                                                        };
                                                    });

                                                const usefulRules = preparedRules.filter((rule) => isUsefulLimeRule(rule, rule.readableRule));
                                                const rulesToShow = usefulRules.length ? usefulRules : preparedRules;

                                                if (!rulesToShow.length) {
                                                    return (
                                                        <p className="text-sm text-muted-foreground">
                                                            Useful LIME rule details are not available right now.
                                                        </p>
                                                    );
                                                }

                                                const maxImpact = getMaxImpact(rulesToShow);
                                                return rulesToShow.map((rule, index) => {
                                                    const isNegative = rule.displayEffect === 'hurts';
                                                    const impactPercent = (Math.abs(rule.impact) / maxImpact) * 100;
                                                    
                                                    return (
                                                        <div
                                                            key={`${rule.rule}-${index}`}
                                                            className={`rounded-lg border p-4 transition-all hover:shadow-md ${
                                                                isNegative 
                                                                    ? 'border-orange-200 bg-orange-50' 
                                                                    : 'border-cyan-200 bg-cyan-50'
                                                            }`}
                                                        >
                                                            <div className="flex gap-4">
                                                                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                                                                    isNegative ? 'bg-orange-200' : 'bg-cyan-200'
                                                                }`}>
                                                                    {isNegative ? (
                                                                        <TrendingDown className="w-5 h-5 text-orange-700" />
                                                                    ) : (
                                                                        <TrendingUp className="w-5 h-5 text-cyan-700" />
                                                                    )}
                                                                </div>
                                                                <div className="flex-grow">
                                                                    <div className="flex items-start justify-between mb-2">
                                                                        <div>
                                                                            <p className={`text-sm font-semibold ${
                                                                                isNegative ? 'text-orange-900' : 'text-cyan-900'
                                                                            }`}>
                                                                                {rule.readableRule}
                                                                            </p>
                                                                            <p className={`text-sm ${isNegative ? 'text-orange-800' : 'text-cyan-800'}`}>
                                                                                {rule.readableSummary}
                                                                            </p>
                                                                        </div>
                                                                        <Badge className={isNegative ? 'bg-orange-600' : 'bg-cyan-600'}>
                                                                            {rule.displayEffect === 'helps' ? '↑ Positive' : '↓ Negative'}
                                                                        </Badge>
                                                                    </div>
                                                                    <div className="mt-3 space-y-2">
                                                                        <div className="flex justify-between items-center text-xs">
                                                                            <span className={`font-medium ${isNegative ? 'text-orange-700' : 'text-cyan-700'}`}>
                                                                                Effect on score
                                                                            </span>
                                                                            <span className={`font-bold text-sm ${isNegative ? 'text-orange-700' : 'text-cyan-700'}`}>
                                                                                {rule.impact >= 0 ? '+' : ''}{rule.impact.toFixed(1)} pts
                                                                            </span>
                                                                        </div>
                                                                        {rule.impact !== 0 && (
                                                                            <div className={`w-full h-2 rounded-full overflow-hidden ${isNegative ? 'bg-orange-200' : 'bg-cyan-200'}`}>
                                                                                <div 
                                                                                    className={`h-full ${isNegative ? 'bg-orange-600' : 'bg-cyan-600'}`}
                                                                                    style={{ width: `${impactPercent}%` }}
                                                                                />
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    );
                                                });
                                            })()}
                                        </>
                                    ) : (
                                        <p className="text-sm text-muted-foreground">LIME rule details are not available right now.</p>
                                    )}
                                </TabsContent>

                                <TabsContent value="advice" className="space-y-4">
                                    {geminiAdvice ? (
                                        <>
                                            {/* Intro explanation */}
                                            <div className="text-xs text-muted-foreground bg-blue-50 border border-blue-200 rounded-lg p-3">
                                                <p><strong>What you're seeing:</strong> Personalized recommendations to improve your credit score based on your financial profile.</p>
                                            </div>

                                            {/* Main advice card */}
                                            <div className="rounded-lg border border-slate-200 overflow-hidden bg-white">
                                                <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-5 py-4 text-white">
                                                    <div className="flex items-center gap-3">
                                                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                                                            <Sparkles className="w-5 h-5" />
                                                        </div>
                                                        <div>
                                                            <h3 className="font-bold text-base">
                                                                {geminiAdvice.source === 'gemini'
                                                                    ? 'AI-Powered Credit Improvement Strategy'
                                                                    : 'Personalized Credit Improvement Strategy'}
                                                            </h3>
                                                            <p className="text-xs text-blue-100 mt-0.5">
                                                                {geminiAdvice.source === 'gemini'
                                                                    ? 'Powered by generative AI'
                                                                    : 'Based on your profile analysis'}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="px-5 py-5 space-y-4">
                                                    {/* Parse and display advice as paragraphs */}
                                                    {(() => {
                                                        const adviceText = geminiAdvice.advice || '';
                                                        // Split by numbered patterns and normalize
                                                        const sections = adviceText
                                                            .split(/\d+\.\s+/)
                                                            .filter(s => s.trim().length > 0)
                                                            .map(s => s.trim());

                                                        if (sections.length > 1) {
                                                            // Has multiple numbered sections
                                                            return (
                                                                <div className="space-y-4">
                                                                    {sections.map((section, idx) => {
                                                                        // Extract title (text until first colon or first sentence)
                                                                        const titleMatch = section.match(/^([^:\.]+)[:\.]/);
                                                                        const title = titleMatch ? titleMatch[1].replace(/\*{1,2}/g, '').trim() : `Point ${idx + 1}`;
                                                                        const content = section.replace(/^\*{1,2}[^:]+\*{0,2}:\s*/, '').trim();

                                                                        return (
                                                                            <div key={`section-${idx}`} className="rounded-lg border border-blue-100 bg-blue-50/30 p-4">
                                                                                <div className="flex gap-3">
                                                                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-bold">
                                                                                        {idx + 1}
                                                                                    </div>
                                                                                    <div className="flex-grow">
                                                                                        <h4 className="font-semibold text-sm text-blue-900 mb-2">
                                                                                            {title}
                                                                                        </h4>
                                                                                        <p className="text-sm text-slate-700 leading-relaxed">
                                                                                            {content.replace(/\*{1,2}([^*]+)\*{1,2}/g, '$1')}
                                                                                        </p>
                                                                                    </div>
                                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            );
                                        } else {
                                            // Single paragraph - display with better formatting
                                            return (
                                                <div className="text-sm text-slate-700 leading-relaxed space-y-3">
                                                    {adviceText.split('\n\n').map((para, idx) => (
                                                        <p key={`para-${idx}`}>{para.replace(/\*{1,2}([^*]+)\*{1,2}/g, '$1')}</p>
                                                    ))}
                                                </div>
                                            );
                                        }
                                    })()}
                                </div>
                            </div>

                            {/* Improvement tips section */}
                            {geminiAdvice.improvementTips?.length ? (
                                <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-5 space-y-4">
                                    <div className="flex items-center gap-2">
                                        <Zap className="w-5 h-5 text-amber-600" />
                                        <h4 className="font-bold text-sm text-amber-900">Quick Action Items</h4>
                                    </div>
                                    <div className="space-y-2">
                                        {geminiAdvice.improvementTips.map((tip, index) => (
                                            <div
                                                key={`tip-${index}`}
                                                className="flex gap-3 p-3 rounded-lg bg-white border border-amber-200 hover:shadow-sm transition-shadow"
                                            >
                                                <div className="flex-shrink-0 mt-0.5">
                                                    <div className="w-5 h-5 rounded-full bg-amber-500 flex items-center justify-center">
                                                        <CheckCircle className="w-4 h-4 text-white" />
                                                    </div>
                                                </div>
                                                <p className="text-sm text-slate-700 flex-grow">{tip}</p>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="flex items-start gap-2 pt-2 border-t border-amber-200">
                                        <ArrowRight className="w-4 h-4 text-amber-700 mt-0.5 flex-shrink-0" />
                                        <p className="text-xs text-amber-800">Start with the items that have the highest impact on improving your credit score.</p>
                                    </div>
                                </div>
                            ) : null}
                        </>
                    ) : (
                        <div className="rounded-lg border border-slate-200 p-4 bg-slate-50">
                            <p className="text-sm text-muted-foreground">
                                Advice is not available right now.
                                            </p>
                                        </div>
                                    )}
                                </TabsContent>
                            </Tabs>
                        </>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};

export default BorrowerDashboard;
