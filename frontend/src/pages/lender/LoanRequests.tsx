import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useAuth } from '@/context/AuthContext';
import { authService, LoanRequestBorrower } from '@/services/authService';
import { toast } from 'sonner';
import { Eye, CheckCircle, SkipForward, FileText } from 'lucide-react';

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
                <DialogContent className="sm:max-w-md">
                    <DialogHeader>
                        <DialogTitle>Review Borrower</DialogTitle>
                        <DialogDescription>Review the borrower's details before making a decision.</DialogDescription>
                    </DialogHeader>
                    {selected && (
                        <div className="grid gap-3 py-4 text-sm">
                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <p className="text-muted-foreground">Name</p>
                                    <p className="font-semibold">{selected.name}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Credit Score</p>
                                    <p className="font-semibold">{selected.creditScore}</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <p className="text-muted-foreground">Risk Level</p>
                                    <div>{riskBadge(selected.risk)}</div>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Monthly Income</p>
                                    <p className="font-semibold">₹{selected.income.toLocaleString('en-IN')}</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <p className="text-muted-foreground">Expecting Loan Amount</p>
                                    <p className="font-semibold">₹{selected.loanAmount.toLocaleString('en-IN')}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Loan Tenure</p>
                                    <p className="font-semibold">{formatTenure(selected.loanTenureYr, selected.loanTenureMon)}</p>
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
