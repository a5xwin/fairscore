import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useAuth } from '@/context/AuthContext';
import { authService, GeminiAdvice, LoanRequestBorrower, ShapExplanation } from '@/services/authService';
import { toast } from 'sonner';
import { Eye, CheckCircle, SkipForward, FileText, Sparkles, ShieldCheck, AlertTriangle } from 'lucide-react';

const riskBadge = (risk: string) => {
    const r = risk.toLowerCase();
    if (r === 'low') return <Badge className="bg-green-100 text-green-800 border-green-200">Low</Badge>;
    if (r === 'medium') return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">Medium</Badge>;
    return <Badge className="bg-red-100 text-red-800 border-red-200">High</Badge>;
};

const formatTenure = (yr: number, mon: number) => {
    const parts: string[] = [];
    if (yr > 0) parts.push(`${yr} yr${yr > 1 ? 's' : ''}`);
    if (mon > 0) parts.push(`${mon} mo${mon > 1 ? 's' : ''}`);
    return parts.join(' ') || '—';
};

const LoanRequests = () => {
    const { user } = useAuth();
    const [requests, setRequests] = useState<LoanRequestBorrower[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Review dialog
    const [selected, setSelected] = useState<LoanRequestBorrower | null>(null);
    const [actionLoading, setActionLoading] = useState<'approve' | 'skip' | null>(null);
    const [explanationLoading, setExplanationLoading] = useState(false);
    const [shapExplanation, setShapExplanation] = useState<ShapExplanation | null>(null);
    const [geminiAdvice, setGeminiAdvice] = useState<GeminiAdvice | null>(null);
    const [shapError, setShapError] = useState('');
    const [geminiError, setGeminiError] = useState('');

    useEffect(() => {
        const fetchRequests = async () => {
            if (!user?.id) return;
            try {
                const data = await authService.getLoanRequests(user.id);
                setRequests(data);
            } catch {
                setError('Failed to load loan requests.');
            } finally {
                setLoading(false);
            }
        };
        fetchRequests();
    }, [user?.id]);

    useEffect(() => {
        const preloadExplanations = async () => {
            if (!selected?.userid) {
                setShapExplanation(null);
                setGeminiAdvice(null);
                setShapError('');
                setGeminiError('');
                return;
            }

            setExplanationLoading(true);
            setShapExplanation(null);
            setGeminiAdvice(null);
            setShapError('');
            setGeminiError('');

            const [shapResult, geminiResult] = await Promise.allSettled([
                authService.getShapExplanation(selected.userid),
                authService.getGeminiAdvice(selected.userid),
            ]);

            if (shapResult.status === 'fulfilled') {
                setShapExplanation(shapResult.value);
            } else {
                const e = shapResult.reason as { response?: { data?: { detail?: string } } };
                setShapError(e?.response?.data?.detail || 'Could not load SHAP factors.');
            }

            if (geminiResult.status === 'fulfilled') {
                setGeminiAdvice(geminiResult.value);
            } else {
                const e = geminiResult.reason as { response?: { data?: { detail?: string } } };
                setGeminiError(e?.response?.data?.detail || 'Could not load AI recommendation.');
            }

            setExplanationLoading(false);
        };

        preloadExplanations();
    }, [selected?.userid]);

    const handleApprove = async () => {
        if (!user?.id || !selected) return;
        setActionLoading('approve');
        try {
            await authService.approveBorrower(user.id, selected.userid);
            toast.success(`${selected.name} approved!`);
            setRequests((prev) => prev.filter((r) => r.userid !== selected.userid));
            setSelected(null);
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string } } };
            toast.error(e?.response?.data?.detail || 'Failed to approve.');
        } finally {
            setActionLoading(null);
        }
    };

    const handleSkip = async () => {
        if (!user?.id || !selected) return;
        setActionLoading('skip');
        try {
            await authService.skipBorrower(user.id, selected.userid);
            toast.info(`${selected.name} skipped.`);
            setRequests((prev) => prev.filter((r) => r.userid !== selected.userid));
            setSelected(null);
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string } } };
            toast.error(e?.response?.data?.detail || 'Failed to skip.');
        } finally {
            setActionLoading(null);
        }
    };

    return (
        <div className="flex-1 space-y-6">
            <h2 className="text-3xl font-bold tracking-tight">Loan Requests</h2>

            {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
            )}

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5 text-primary" />
                        Pending Requests ({requests.length})
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="space-y-3">
                            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
                        </div>
                    ) : requests.length === 0 ? (
                        <p className="text-center text-muted-foreground py-8">No pending loan requests.</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Name</TableHead>
                                        <TableHead className="text-center">Credit Score</TableHead>
                                        <TableHead className="text-center">Risk Level</TableHead>
                                        <TableHead className="text-right">Action</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {requests.map((req) => (
                                        <TableRow key={req.userid}>
                                            <TableCell className="font-medium">{req.name}</TableCell>
                                            <TableCell className="text-center">{req.creditScore}</TableCell>
                                            <TableCell className="text-center">{riskBadge(req.risk)}</TableCell>
                                            <TableCell className="text-right">
                                                <Button size="sm" variant="outline" onClick={() => setSelected(req)}>
                                                    <Eye className="h-4 w-4 mr-1" /> Review
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Review Dialog */}
            <Dialog open={!!selected} onOpenChange={(open) => { if (!open) setSelected(null); }}>
                <DialogContent className="sm:max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>Review Borrower</DialogTitle>
                        <DialogDescription>Review the borrower's details before making a decision.</DialogDescription>
                    </DialogHeader>
                    {selected && (
                        <div className="grid gap-5 py-4 text-sm">
                            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                                <div>
                                    <p className="text-muted-foreground">Name</p>
                                    <p className="font-semibold">{selected.name}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Credit Score</p>
                                    <p className="font-semibold">{selected.creditScore}</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                                <div>
                                    <p className="text-muted-foreground">Risk Level</p>
                                    <div>{riskBadge(selected.risk)}</div>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Monthly Income</p>
                                    <p className="font-semibold">₹{selected.income.toLocaleString('en-IN')}</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                                <div>
                                    <p className="text-muted-foreground">Expecting Loan Amount</p>
                                    <p className="font-semibold">₹{selected.loanAmount.toLocaleString('en-IN')}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Loan Tenure</p>
                                    <p className="font-semibold">{formatTenure(selected.loanTenureYr, selected.loanTenureMon)}</p>
                                </div>
                            </div>

                            <div className="rounded-lg border p-4 space-y-4">
                                <div className="flex items-center justify-between">
                                    <h4 className="font-semibold flex items-center gap-2">
                                        <ShieldCheck className="h-4 w-4 text-primary" />
                                        Score & Risk Explanation
                                    </h4>
                                    {explanationLoading && <span className="text-xs text-muted-foreground">Loading analysis...</span>}
                                </div>

                                <div className="space-y-3">
                                    <h5 className="text-sm font-medium">SHAP Key Factors</h5>
                                    {explanationLoading && !shapExplanation ? (
                                        <div className="space-y-2">
                                            {[1, 2, 3].map((i) => (
                                                <Skeleton key={i} className="h-8 w-full" />
                                            ))}
                                        </div>
                                    ) : shapError ? (
                                        <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-amber-900 flex items-start gap-2">
                                            <AlertTriangle className="h-4 w-4 mt-0.5" />
                                            <span>{shapError}</span>
                                        </div>
                                    ) : shapExplanation?.topFactors?.length ? (
                                        <div className="space-y-2">
                                            {shapExplanation.topFactors.slice(0, 5).map((factor, idx, arr) => {
                                                const maxImpact = Math.max(...arr.map((f) => Math.abs(f.impact)), 1);
                                                const width = Math.max(8, (Math.abs(factor.impact) / maxImpact) * 100);
                                                const positive = factor.direction === 'helps';

                                                return (
                                                    <div key={`${factor.feature}-${idx}`} className="space-y-1">
                                                        <div className="flex items-center justify-between gap-2">
                                                            <span className="font-medium text-xs sm:text-sm">{factor.feature}</span>
                                                            <span className={`text-xs font-medium ${positive ? 'text-green-700' : 'text-red-700'}`}>
                                                                {positive ? 'Helps score' : 'Hurts score'}
                                                            </span>
                                                        </div>
                                                        <div className="h-2 rounded bg-muted overflow-hidden">
                                                            <div
                                                                className={`h-full ${positive ? 'bg-green-500' : 'bg-red-500'}`}
                                                                style={{ width: `${width}%` }}
                                                            />
                                                        </div>
                                                        <p className="text-xs text-muted-foreground">{factor.summary}</p>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    ) : (
                                        <p className="text-muted-foreground text-sm">No SHAP factors available for this borrower.</p>
                                    )}
                                </div>

                                <div className="space-y-2">
                                    <h5 className="text-sm font-medium flex items-center gap-2">
                                        <Sparkles className="h-4 w-4 text-primary" />
                                        AI Recommendation
                                    </h5>
                                    {explanationLoading && !geminiAdvice ? (
                                        <Skeleton className="h-16 w-full" />
                                    ) : geminiError ? (
                                        <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-amber-900 flex items-start gap-2">
                                            <AlertTriangle className="h-4 w-4 mt-0.5" />
                                            <span>{geminiError}</span>
                                        </div>
                                    ) : geminiAdvice ? (
                                        <div className="rounded-md bg-muted/50 p-3 space-y-2">
                                            <div className="flex items-center justify-between">
                                                <span className="text-xs text-muted-foreground">Advice source</span>
                                                <Badge variant="outline" className="text-xs">
                                                    {geminiAdvice.source === 'gemini' ? 'Gemini' : 'Fallback'}
                                                </Badge>
                                            </div>
                                            <p className="text-sm leading-relaxed whitespace-pre-wrap">{geminiAdvice.advice}</p>
                                            {geminiAdvice.improvementTips?.length > 0 && (
                                                <div>
                                                    <p className="text-xs font-medium text-muted-foreground mb-1">Improvement Tips</p>
                                                    <ul className="list-disc pl-5 space-y-1 text-xs text-muted-foreground">
                                                        {geminiAdvice.improvementTips.slice(0, 4).map((tip, idx) => (
                                                            <li key={idx}>{tip}</li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <p className="text-muted-foreground text-sm">No AI recommendation available for this borrower.</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                    <DialogFooter className="flex gap-2 sm:justify-between">
                        <Button
                            variant="outline"
                            onClick={handleSkip}
                            disabled={actionLoading !== null}
                        >
                            <SkipForward className="h-4 w-4 mr-1" />
                            {actionLoading === 'skip' ? 'Skipping...' : 'Skip'}
                        </Button>
                        <Button
                            onClick={handleApprove}
                            disabled={actionLoading !== null}
                        >
                            <CheckCircle className="h-4 w-4 mr-1" />
                            {actionLoading === 'approve' ? 'Approving...' : 'Approve'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
};

export default LoanRequests;
