import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/context/AuthContext';
import {
    authService,
    CreditInfo,
    ScoreReasons,
    GeminiAdvice,
} from '@/services/authService';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { ShieldCheck, TrendingUp, Wallet, AlertTriangle, CheckCircle, Info, Sparkles, ArrowRight, Zap } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

const riskConfig: Record<string, { color: string; icon: typeof ShieldCheck; label: string }> = {
    low: { color: 'bg-green-100 text-green-800 border-green-200', icon: CheckCircle, label: 'Low Risk' },
    medium: { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: AlertTriangle, label: 'Medium Risk' },
    high: { color: 'bg-red-100 text-red-800 border-red-200', icon: AlertTriangle, label: 'High Risk' },
};

type AdviceBlock = {
    title: string;
    body: string;
    action: string;
    rationale: string;
};

const cleanAdviceText = (text: string) => {
    return String(text || '')
        .replace(/\r/g, '')
        .replace(/\*\*([^*]+)\*\*/g, '$1')
        .replace(/\*([^*]+)\*/g, '$1')
        .replace(/[ \t]+/g, ' ')
        .trim();
};

const looksLikeActionSentence = (sentence: string) => {
    const normalized = sentence.trim().toLowerCase();
    const actionStarts = [
        'focus',
        'pay',
        'avoid',
        'maintain',
        'consider',
        'review',
        'reduce',
        'increase',
        'build',
        'keep',
        'monitor',
        'improve',
        'establish',
        'diversify',
        'open',
        'correct',
        'set up',
        'start',
    ];
    return actionStarts.some((prefix) => normalized.startsWith(prefix));
};

const chooseActionAndRationale = (body: string, fallbackTitle: string) => {
    const sentenceParts = body
        .split(/(?<=[.!?])\s+/)
        .map((part) => part.trim())
        .filter(Boolean);

    if (!sentenceParts.length) {
        return {
            action: fallbackTitle,
            rationale: 'This can strengthen your credit profile over time.',
        };
    }

    const firstActionIndex = sentenceParts.findIndex((sentence) => looksLikeActionSentence(sentence));
    const action = firstActionIndex >= 0 ? sentenceParts[firstActionIndex] : sentenceParts[0];
    const rationaleParts = sentenceParts.filter((_, idx) => idx !== (firstActionIndex >= 0 ? firstActionIndex : 0));
    const rationale = rationaleParts.join(' ').trim() || 'This directly improves your creditworthiness over time.';

    return { action, rationale };
};

const splitAdviceBlocks = (rawText: string): AdviceBlock[] => {
    const cleaned = cleanAdviceText(rawText);
    if (!cleaned) return [];

    const numberedChunks = cleaned
        .split(/(?:^|\n)\s*\d+\.\s+/)
        .map((chunk) => chunk.trim())
        .filter(Boolean);

    const chunks = numberedChunks.length > 1
        ? numberedChunks
        : cleaned
            .split(/\n{2,}/)
            .map((chunk) => chunk.trim())
            .filter(Boolean);

    const blocks = chunks.map((chunk, index) => {
        const line = chunk.replace(/\n+/g, ' ').trim();
        const colonIndex = line.indexOf(':');

        let title = `Action ${index + 1}`;
        let body = line;

        if (colonIndex > 0 && colonIndex < 90) {
            title = line.slice(0, colonIndex).trim();
            body = line.slice(colonIndex + 1).trim();
        } else {
            const sentenceParts = line.split(/(?<=[.!?])\s+/).filter(Boolean);
            if (sentenceParts.length > 1) {
                title = sentenceParts[0].replace(/[.!?]+$/, '').trim();
                body = sentenceParts.slice(1).join(' ').trim();
            }
        }

        const titleLower = title.toLowerCase();
        const bodyLower = body.toLowerCase();
        if (bodyLower === titleLower || bodyLower.startsWith(`${titleLower}.`) || bodyLower.startsWith(titleLower)) {
            body = '';
        }

        const { action, rationale } = chooseActionAndRationale(body, title);

        // If title is generic (Action 1), derive a better heading from the action sentence.
        if (/^action\s+\d+$/i.test(title)) {
            const fallbackTitle = action
                .split(/[,.;:]/)
                .map((part) => part.trim())
                .find(Boolean);
            if (fallbackTitle) {
                title = fallbackTitle;
            }
        }

        return {
            title,
            body,
            action,
            rationale,
        };
    });

    const filteredBlocks = blocks.filter((block) => {
        const combined = `${block.title} ${block.body}`.toLowerCase();
        return !(
            combined.includes('here are') &&
            combined.includes('practical actions')
        );
    });

    return filteredBlocks.length ? filteredBlocks : blocks;
};

const BorrowerDashboard = () => {
    const { user } = useAuth();
    const [creditInfo, setCreditInfo] = useState<CreditInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [scoreReasons, setScoreReasons] = useState<ScoreReasons | null>(null);
    const [geminiAdvice, setGeminiAdvice] = useState<GeminiAdvice | null>(null);
    const [explanationLoading, setExplanationLoading] = useState(true);
    const [explanationErrors, setExplanationErrors] = useState<string[]>([]);

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

            const [reasonsResult, adviceResult] = await Promise.allSettled([
                authService.getScoreReasons(user.id),
                authService.getScoreAdvice(user.id),
            ]);

            const errors: string[] = [];

            if (reasonsResult.status === 'fulfilled') {
                setScoreReasons(reasonsResult.value);
            } else {
                errors.push('Score reasons are unavailable right now.');
            }

            if (adviceResult.status === 'fulfilled') {
                setGeminiAdvice(adviceResult.value);
            } else {
                errors.push('Improvement advice is unavailable right now.');
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
                    <CardTitle>Score Reasons And Improvement Advice</CardTitle>
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

                            <Tabs defaultValue="reasons" className="w-full">
                                <TabsList className="grid w-full grid-cols-2">
                                    <TabsTrigger value="reasons">Reasons for Score</TabsTrigger>
                                    <TabsTrigger value="advice">Advice</TabsTrigger>
                                </TabsList>

                                <TabsContent value="reasons" className="space-y-3">
                                    {scoreReasons?.combinedReasons?.length ? (
                                        <>
                                            <div className="rounded-lg border border-indigo-200 bg-indigo-50/70 p-4 text-sm text-indigo-900 space-y-2">
                                                <div className="flex items-center justify-between gap-3">
                                                    <p className="font-semibold">Combined score explanation</p>
                                                    {scoreReasons?.source ? (
                                                        <span className="text-[11px] uppercase tracking-wide px-2 py-1 rounded-full bg-white/80 border border-indigo-200 text-indigo-700">
                                                            {scoreReasons.source === 'gemini' ? 'Gemini generated' : 'Fallback generated'}
                                                        </span>
                                                    ) : null}
                                                </div>
                                                <p>{scoreReasons.overview || 'These reasons combine broad model influence and your profile-specific patterns.'}</p>
                                            </div>

                                            {scoreReasons.combinedReasons.map((reason, index) => {
                                                const isNegative = reason.direction === 'hurts';
                                                return (
                                                    <div
                                                        key={`${reason.feature}-${index}`}
                                                        className={`rounded-lg border p-4 ${
                                                            isNegative ? 'border-red-200 bg-red-50/80' : 'border-emerald-200 bg-emerald-50/80'
                                                        }`}
                                                    >
                                                        <div className="flex items-start justify-between gap-4 mb-2">
                                                            <h4 className={`font-semibold ${isNegative ? 'text-red-900' : 'text-emerald-900'}`}>
                                                                {reason.feature}
                                                            </h4>
                                                            <Badge className={isNegative ? 'bg-red-600' : 'bg-emerald-600'}>
                                                                {isNegative ? 'Hurts score' : 'Helps score'}
                                                            </Badge>
                                                        </div>
                                                        <p className={`text-sm ${isNegative ? 'text-red-800' : 'text-emerald-800'}`}>
                                                            {reason.explanation}
                                                        </p>
                                                        <p className={`mt-2 text-xs font-medium ${isNegative ? 'text-red-700' : 'text-emerald-700'}`}>
                                                            Average impact: {Math.abs(reason.impact).toFixed(2)}
                                                        </p>
                                                    </div>
                                                );
                                            })}
                                        </>
                                    ) : (
                                        <p className="text-sm text-muted-foreground">Combined reason details are not available right now.</p>
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
                                                    {(() => {
                                                        const blocks = splitAdviceBlocks(geminiAdvice.advice || '');
                                                        if (!blocks.length) {
                                                            return (
                                                                <p className="text-sm text-slate-700 leading-relaxed">
                                                                    {cleanAdviceText(geminiAdvice.advice || 'No advice available right now.')}
                                                                </p>
                                                            );
                                                        }

                                                        return (
                                                            <div className="space-y-3">
                                                                {blocks.map((block, idx) => (
                                                                    <div key={`advice-block-${idx}`} className="rounded-lg border border-blue-100 bg-blue-50/30 p-4">
                                                                        <div className="flex gap-3">
                                                                            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-bold">
                                                                                {idx + 1}
                                                                            </div>
                                                                            <div className="flex-grow">
                                                                                <h4 className="font-semibold text-sm text-blue-900 mb-1">
                                                                                    {block.title}
                                                                                </h4>
                                                                                <div className="space-y-2 text-sm text-slate-700 leading-relaxed">
                                                                                    <div>
                                                                                        <p className="text-[11px] uppercase tracking-wide text-blue-700 font-semibold">What to do</p>
                                                                                        <p>{block.action}</p>
                                                                                    </div>
                                                                                    {block.rationale ? (
                                                                                        <div>
                                                                                            <p className="text-[11px] uppercase tracking-wide text-blue-700 font-semibold">Why it helps</p>
                                                                                            <p>{block.rationale}</p>
                                                                                        </div>
                                                                                    ) : null}
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        );
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
