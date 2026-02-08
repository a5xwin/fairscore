import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/context/AuthContext';
import { authService, ApprovedLender } from '@/services/authService';
import { Skeleton } from '@/components/ui/skeleton';
import { CheckCircle } from 'lucide-react';

const Approvals = () => {
    const { user } = useAuth();
    const [approvedLenders, setApprovedLenders] = useState<ApprovedLender[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchApprovals = async () => {
            if (!user?.id) return;
            try {
                const data = await authService.getApprovedLenders(user.id);
                setApprovedLenders(data);
            } catch {
                setError('Failed to load approved lenders.');
            } finally {
                setLoading(false);
            }
        };
        fetchApprovals();
    }, [user?.id]);

    return (
        <div className="flex-1 space-y-6">
            <h2 className="text-3xl font-bold tracking-tight">Approvals</h2>

            {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
            )}

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        Approved Lenders ({approvedLenders.length})
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="space-y-3">
                            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
                        </div>
                    ) : approvedLenders.length === 0 ? (
                        <p className="text-center text-muted-foreground py-8">
                            No approved lenders yet. Apply to lenders from the Apply Loan page.
                        </p>
                    ) : (
                        <div className="overflow-x-auto">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Lender Name</TableHead>
                                        <TableHead>Type</TableHead>
                                        <TableHead className="text-right">Capacity (₹)</TableHead>
                                        <TableHead className="text-right">Loan Range (₹)</TableHead>
                                        <TableHead className="text-right">Interest (%)</TableHead>
                                        <TableHead className="text-center">Status</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {approvedLenders.map((lender) => (
                                        <TableRow key={lender.lenderId}>
                                            <TableCell className="font-medium">{lender.Name}</TableCell>
                                            <TableCell>{lender.type}</TableCell>
                                            <TableCell className="text-right">
                                                ₹{lender.capacity.toLocaleString('en-IN')}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                ₹{lender.loanAmountFrom.toLocaleString('en-IN')} – ₹{lender.loanAmountTo.toLocaleString('en-IN')}
                                            </TableCell>
                                            <TableCell className="text-right">{lender.interest}%</TableCell>
                                            <TableCell className="text-center">
                                                <Badge className="bg-green-100 text-green-800 border-green-200">
                                                    Approved
                                                </Badge>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};

export default Approvals;
