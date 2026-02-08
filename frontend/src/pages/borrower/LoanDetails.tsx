import { useEffect, useState } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAuth } from '@/context/AuthContext';
import { authService, LoanInfo } from '@/services/authService';
import { loanPurposes } from '@/data/locationData';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { Pencil, Save, X } from 'lucide-react';

const LoanDetails = () => {
    const { user } = useAuth();
    const [loanInfo, setLoanInfo] = useState<LoanInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    // Edit form state
    const [loanAmount, setLoanAmount] = useState('');
    const [loanTenureYr, setLoanTenureYr] = useState('');
    const [loanTenureMon, setLoanTenureMon] = useState('');
    const [purpose, setPurpose] = useState('');

    useEffect(() => {
        const fetchLoanInfo = async () => {
            if (!user?.id) return;
            try {
                const data = await authService.getLoanInfo(user.id);
                setLoanInfo(data);
                setLoanAmount(String(data.loanAmount));
                setLoanTenureYr(String(data.loanTenureYr));
                setLoanTenureMon(String(data.loanTenureMon));
                setPurpose(data.purpose);
            } catch {
                setError('Failed to load loan details.');
            } finally {
                setLoading(false);
            }
        };
        fetchLoanInfo();
    }, [user?.id]);

    const handleCancel = () => {
        if (loanInfo) {
            setLoanAmount(String(loanInfo.loanAmount));
            setLoanTenureYr(String(loanInfo.loanTenureYr));
            setLoanTenureMon(String(loanInfo.loanTenureMon));
            setPurpose(loanInfo.purpose);
        }
        setEditing(false);
    };

    const handleSave = async () => {
        if (!user?.id) return;
        if (!loanAmount || loanTenureYr === '' || loanTenureMon === '' || !purpose) {
            toast.error('Please fill all fields.');
            return;
        }
        setSaving(true);
        try {
            await authService.updateLoanInfo({
                userid: user.id,
                loanAmount: Number(loanAmount),
                loanTenureYr: Number(loanTenureYr),
                loanTenureMon: Number(loanTenureMon),
                purpose,
            });
            setLoanInfo({
                loanAmount: Number(loanAmount),
                loanTenureYr: Number(loanTenureYr),
                loanTenureMon: Number(loanTenureMon),
                purpose,
            });
            setEditing(false);
            toast.success('Loan details updated successfully!');
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string } } };
            toast.error(e?.response?.data?.detail || 'Failed to update loan details.');
        } finally {
            setSaving(false);
        }
    };

    const formatTenure = () => {
        const yrs = loanInfo?.loanTenureYr ?? 0;
        const mons = loanInfo?.loanTenureMon ?? 0;
        const parts: string[] = [];
        if (yrs > 0) parts.push(`${yrs} yr${yrs > 1 ? 's' : ''}`);
        if (mons > 0) parts.push(`${mons} mo${mons > 1 ? 's' : ''}`);
        return parts.join(' ') || '—';
    };

    return (
        <div className="flex-1 space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Loan Details</h2>
                {!loading && !editing && (
                    <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                        <Pencil className="h-4 w-4 mr-1" /> Edit
                    </Button>
                )}
            </div>

            {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
            )}

            <Card>
                <CardHeader>
                    <CardTitle>Your Loan Request</CardTitle>
                    <CardDescription>
                        {editing ? 'Update your loan details below.' : 'Details you submitted during onboarding.'}
                    </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                    {loading ? (
                        <div className="space-y-4">
                            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
                        </div>
                    ) : editing ? (
                        <>
                            <div className="space-y-2">
                                <Label htmlFor="loanAmount">Loan Amount (₹)</Label>
                                <Input
                                    id="loanAmount"
                                    type="number"
                                    min={0}
                                    value={loanAmount}
                                    onChange={(e) => setLoanAmount(e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Loan Tenure</Label>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1">
                                        <Label className="text-xs text-muted-foreground">Years</Label>
                                        <Input
                                            type="number"
                                            min={0}
                                            max={30}
                                            value={loanTenureYr}
                                            onChange={(e) => setLoanTenureYr(e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <Label className="text-xs text-muted-foreground">Months</Label>
                                        <Input
                                            type="number"
                                            min={0}
                                            max={11}
                                            value={loanTenureMon}
                                            onChange={(e) => setLoanTenureMon(e.target.value)}
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label>Purpose</Label>
                                <Select value={purpose} onValueChange={setPurpose}>
                                    <SelectTrigger><SelectValue placeholder="Select purpose" /></SelectTrigger>
                                    <SelectContent>
                                        {loanPurposes.map((p) => (
                                            <SelectItem key={p} value={p}>{p}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </>
                    ) : (
                        <div className="grid gap-4 sm:grid-cols-2">
                            <div>
                                <p className="text-sm text-muted-foreground">Loan Amount</p>
                                <p className="text-lg font-semibold">₹{(loanInfo?.loanAmount ?? 0).toLocaleString('en-IN')}</p>
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground">Loan Tenure</p>
                                <p className="text-lg font-semibold">{formatTenure()}</p>
                            </div>
                            <div className="sm:col-span-2">
                                <p className="text-sm text-muted-foreground">Purpose</p>
                                <p className="text-lg font-semibold">{loanInfo?.purpose ?? '—'}</p>
                            </div>
                        </div>
                    )}
                </CardContent>

                {editing && (
                    <CardFooter className="flex justify-end gap-2">
                        <Button variant="outline" onClick={handleCancel} disabled={saving}>
                            <X className="h-4 w-4 mr-1" /> Cancel
                        </Button>
                        <Button onClick={handleSave} disabled={saving}>
                            <Save className="h-4 w-4 mr-1" /> {saving ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </CardFooter>
                )}
            </Card>
        </div>
    );
};

export default LoanDetails;
