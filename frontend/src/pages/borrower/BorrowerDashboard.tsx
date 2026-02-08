import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/context/AuthContext';
import { authService, CreditInfo } from '@/services/authService';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { ShieldCheck, TrendingUp, Wallet, AlertTriangle, CheckCircle, Info } from 'lucide-react';

const riskConfig: Record<string, { color: string; icon: typeof ShieldCheck; label: string }> = {
    low: { color: 'bg-green-100 text-green-800 border-green-200', icon: CheckCircle, label: 'Low Risk' },
    medium: { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: AlertTriangle, label: 'Medium Risk' },
    high: { color: 'bg-red-100 text-red-800 border-red-200', icon: AlertTriangle, label: 'High Risk' },
};

const BorrowerDashboard = () => {
    const { user } = useAuth();
    const [creditInfo, setCreditInfo] = useState<CreditInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

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
        fetchCreditInfo();
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
        </div>
    );
};

export default BorrowerDashboard;
