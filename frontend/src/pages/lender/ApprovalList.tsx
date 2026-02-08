import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import { authService, ApprovedBorrower } from '@/services/authService';
import { CheckCircle, Eye } from 'lucide-react';

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

const ApprovalList = () => {
    const { user } = useAuth();
    const [borrowers, setBorrowers] = useState<ApprovedBorrower[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selected, setSelected] = useState<ApprovedBorrower | null>(null);

    useEffect(() => {
        const fetchApproved = async () => {
            if (!user?.id) return;
            try {
                const data = await authService.getApprovedBorrowers(user.id);
                setBorrowers(data);
            } catch {
                setError('Failed to load approved borrowers.');
            } finally {
                setLoading(false);
            }
        };
        fetchApproved();
    }, [user?.id]);

    return (
        <div className="flex-1 space-y-6">
            <h2 className="text-3xl font-bold tracking-tight">Approval List</h2>

            {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
            )}

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        Approved Borrowers ({borrowers.length})
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="space-y-3">
                            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
                        </div>
                    ) : borrowers.length === 0 ? (
                        <p className="text-center text-muted-foreground py-8">No approved borrowers yet.</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Name</TableHead>
                                        <TableHead className="text-center">Credit Score</TableHead>
                                        <TableHead className="text-center">Risk</TableHead>
                                        <TableHead className="text-right">Income (₹)</TableHead>
                                        <TableHead className="text-right">Loan Amount (₹)</TableHead>
                                        <TableHead className="text-center">Tenure</TableHead>
                                        <TableHead className="text-right">Action</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {borrowers.map((b) => (
                                        <TableRow key={b.userid}>
                                            <TableCell className="font-medium">{b.name}</TableCell>
                                            <TableCell className="text-center">{b.creditScore}</TableCell>
                                            <TableCell className="text-center">{riskBadge(b.risk)}</TableCell>
                                            <TableCell className="text-right">₹{b.income.toLocaleString('en-IN')}</TableCell>
                                            <TableCell className="text-right">₹{b.loanAmount.toLocaleString('en-IN')}</TableCell>
                                            <TableCell className="text-center">{formatTenure(b.loanTenureYr, b.loanTenureMon)}</TableCell>
                                            <TableCell className="text-right">
                                                <Button size="sm" variant="outline" onClick={() => setSelected(b)}>
                                                    <Eye className="h-4 w-4 mr-1" /> View
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

            {/* Detail Dialog */}
            <Dialog open={!!selected} onOpenChange={(open) => { if (!open) setSelected(null); }}>
                <DialogContent className="sm:max-w-lg">
                    <DialogHeader>
                        <DialogTitle>Borrower Profile</DialogTitle>
                    </DialogHeader>
                    {selected && (
                        <div className="grid gap-3 py-4 text-sm">
                            <div className="grid grid-cols-2 gap-y-3 gap-x-6">
                                <div>
                                    <p className="text-muted-foreground">Name</p>
                                    <p className="font-semibold">{selected.name}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Email</p>
                                    <p className="font-semibold">{selected.email}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Age</p>
                                    <p className="font-semibold">{selected.age}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Gender</p>
                                    <p className="font-semibold">{selected.gender}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">State</p>
                                    <p className="font-semibold">{selected.state}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">City</p>
                                    <p className="font-semibold">{selected.city}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Occupation</p>
                                    <p className="font-semibold">{selected.occupation}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Credit Score</p>
                                    <p className="font-semibold">{selected.creditScore}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Risk Level</p>
                                    <div>{riskBadge(selected.risk)}</div>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Monthly Income</p>
                                    <p className="font-semibold">₹{selected.income.toLocaleString('en-IN')}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Existing Loans</p>
                                    <p className="font-semibold">{selected.loanNo}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">LTV Ratio</p>
                                    <p className="font-semibold">{selected.ltvRatio}%</p>
                                </div>
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
                </DialogContent>
            </Dialog>
        </div>
    );
};

export default ApprovalList;
