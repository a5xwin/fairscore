import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useAuth } from '@/context/AuthContext';
import { authService, LenderInfo } from '@/services/authService';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { Search, Send } from 'lucide-react';

const ApplyLoan = () => {
    const { user } = useAuth();
    const [lenders, setLenders] = useState<LenderInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [applyingId, setApplyingId] = useState<string | null>(null);

    // Filters
    const [searchName, setSearchName] = useState('');
    const [filterType, setFilterType] = useState('all');

    useEffect(() => {
        const fetchLenders = async () => {
            if (!user?.id) return;
            try {
                const data = await authService.getLenderInfo(user.id);
                setLenders(data);
            } catch {
                setError('Failed to load lender information.');
            } finally {
                setLoading(false);
            }
        };
        fetchLenders();
    }, [user?.id]);

    const handleApply = async (lenderid: string) => {
        if (!user?.id) return;
        setApplyingId(lenderid);
        try {
            await authService.applyToLender(user.id, lenderid);
            toast.success('Application submitted successfully!');
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string } } };
            toast.error(e?.response?.data?.detail || 'Failed to apply. Please try again.');
        } finally {
            setApplyingId(null);
        }
    };

    // Derive unique lender types for filter dropdown
    const lenderTypes = Array.from(new Set(lenders.map((l) => l.type)));

    const filteredLenders = lenders.filter((l) => {
        const matchesName = l.name.toLowerCase().includes(searchName.toLowerCase());
        const matchesType = filterType === 'all' || l.type === filterType;
        return matchesName && matchesType;
    });

    return (
        <div className="flex-1 space-y-6">
            <h2 className="text-3xl font-bold tracking-tight">Apply for a Loan</h2>

            {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
            )}

            {/* Search & Filter */}
            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col sm:flex-row gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search lender by name..."
                                className="pl-9"
                                value={searchName}
                                onChange={(e) => setSearchName(e.target.value)}
                            />
                        </div>
                        <Select value={filterType} onValueChange={setFilterType}>
                            <SelectTrigger className="w-full sm:w-[200px]">
                                <SelectValue placeholder="Filter by type" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Types</SelectItem>
                                {lenderTypes.map((t) => (
                                    <SelectItem key={t} value={t}>{t}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>
            </Card>

            {/* Lender Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Available Lenders ({filteredLenders.length})</CardTitle>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="space-y-3">
                            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
                        </div>
                    ) : filteredLenders.length === 0 ? (
                        <p className="text-center text-muted-foreground py-8">No lenders found matching your criteria.</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Name</TableHead>
                                        <TableHead>Type</TableHead>
                                        <TableHead className="text-right">Loan Range (₹)</TableHead>
                                        <TableHead className="text-right">Interest (%)</TableHead>
                                        <TableHead className="text-right">Action</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredLenders.map((lender) => (
                                        <TableRow key={lender.lenderid}>
                                            <TableCell className="font-medium">{lender.name}</TableCell>
                                            <TableCell>{lender.type}</TableCell>
                                            <TableCell className="text-right">
                                                ₹{lender.loanAmountFrom.toLocaleString('en-IN')} – ₹{lender.loanAmountTo.toLocaleString('en-IN')}
                                            </TableCell>
                                            <TableCell className="text-right">{lender.Interest}%</TableCell>
                                            <TableCell className="text-right">
                                                <Button
                                                    size="sm"
                                                    onClick={() => handleApply(lender.lenderid)}
                                                    disabled={applyingId === lender.lenderid}
                                                >
                                                    <Send className="h-4 w-4 mr-1" />
                                                    {applyingId === lender.lenderid ? 'Applying...' : 'Apply'}
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
        </div>
    );
};

export default ApplyLoan;
