import { useEffect, useState } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useAuth } from '@/context/AuthContext';
import { authService, LenderDetails } from '@/services/authService';
import { toast } from 'sonner';
import { Pencil, Save, X, User, Building2, Wallet, IndianRupee, Percent } from 'lucide-react';

const LenderDashboard = () => {
    const { user } = useAuth();
    const [details, setDetails] = useState<LenderDetails | null>(null);
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    // Editable fields
    const [capacity, setCapacity] = useState('');
    const [loanAmountFrom, setLoanAmountFrom] = useState('');
    const [loanAmountTo, setLoanAmountTo] = useState('');
    const [interest, setInterest] = useState('');

    useEffect(() => {
        const fetchDetails = async () => {
            if (!user?.id) return;
            try {
                const data = await authService.getLenderDetails(user.id);
                setDetails(data);
                setCapacity(String(data.capacity));
                setLoanAmountFrom(String(data.loanAmountFrom));
                setLoanAmountTo(String(data.loanAmountTo));
                setInterest(String(data.interest));
            } catch {
                setError('Failed to load lender details.');
            } finally {
                setLoading(false);
            }
        };
        fetchDetails();
    }, [user?.id]);

    const handleCancel = () => {
        if (details) {
            setCapacity(String(details.capacity));
            setLoanAmountFrom(String(details.loanAmountFrom));
            setLoanAmountTo(String(details.loanAmountTo));
            setInterest(String(details.interest));
        }
        setEditing(false);
    };

    const handleSave = async () => {
        if (!user?.id) return;
        if (!capacity || !loanAmountFrom || !loanAmountTo || !interest) {
            toast.error('Please fill all fields.');
            return;
        }
        if (Number(loanAmountFrom) >= Number(loanAmountTo)) {
            toast.error('Loan range "From" must be less than "To".');
            return;
        }
        setSaving(true);
        try {
            await authService.updateLenderDetails({
                lenderID: user.id,
                capacity: Number(capacity),
                loanAmountFrom: Number(loanAmountFrom),
                loanAmountTo: Number(loanAmountTo),
                interest: Number(interest),
            });
            setDetails((prev) =>
                prev
                    ? {
                          ...prev,
                          capacity: Number(capacity),
                          loanAmountFrom: Number(loanAmountFrom),
                          loanAmountTo: Number(loanAmountTo),
                          interest: Number(interest),
                      }
                    : prev
            );
            setEditing(false);
            toast.success('Details updated successfully!');
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string } } };
            toast.error(e?.response?.data?.detail || 'Failed to update details.');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="flex-1 space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
                {!loading && !editing && (
                    <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                        <Pencil className="h-4 w-4 mr-1" /> Edit
                    </Button>
                )}
            </div>

            {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
            )}

            {/* Summary cards (read-only) */}
            <div className="grid gap-4 md:grid-cols-2">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Name</CardTitle>
                        <User className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        {loading ? <Skeleton className="h-8 w-40" /> : (
                            <div className="text-2xl font-bold">{details?.name ?? '—'}</div>
                        )}
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Type</CardTitle>
                        <Building2 className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        {loading ? <Skeleton className="h-8 w-40" /> : (
                            <Badge variant="outline" className="text-base px-3 py-1">{details?.type ?? '—'}</Badge>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Editable details card */}
            <Card>
                <CardHeader>
                    <CardTitle>Lending Configuration</CardTitle>
                    <CardDescription>
                        {editing ? 'Update your lending parameters below.' : 'Your current lending parameters.'}
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
                                <Label htmlFor="capacity">Lending Capacity (₹)</Label>
                                <Input id="capacity" type="number" min={0} value={capacity} onChange={(e) => setCapacity(e.target.value)} />
                            </div>
                            <div className="space-y-2">
                                <Label>Loan Range (₹)</Label>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1">
                                        <Label className="text-xs text-muted-foreground">From</Label>
                                        <Input type="number" min={0} value={loanAmountFrom} onChange={(e) => setLoanAmountFrom(e.target.value)} />
                                    </div>
                                    <div className="space-y-1">
                                        <Label className="text-xs text-muted-foreground">To</Label>
                                        <Input type="number" min={0} value={loanAmountTo} onChange={(e) => setLoanAmountTo(e.target.value)} />
                                    </div>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="interest">Interest Rate (%)</Label>
                                <Input id="interest" type="number" step="0.01" min={0} max={100} value={interest} onChange={(e) => setInterest(e.target.value)} />
                            </div>
                        </>
                    ) : (
                        <div className="grid gap-4 sm:grid-cols-2">
                            <div className="flex items-start gap-3">
                                <Wallet className="h-5 w-5 text-muted-foreground mt-0.5" />
                                <div>
                                    <p className="text-sm text-muted-foreground">Lending Capacity</p>
                                    <p className="text-lg font-semibold">₹{(details?.capacity ?? 0).toLocaleString('en-IN')}</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <IndianRupee className="h-5 w-5 text-muted-foreground mt-0.5" />
                                <div>
                                    <p className="text-sm text-muted-foreground">Loan Range</p>
                                    <p className="text-lg font-semibold">
                                        ₹{(details?.loanAmountFrom ?? 0).toLocaleString('en-IN')} – ₹{(details?.loanAmountTo ?? 0).toLocaleString('en-IN')}
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <Percent className="h-5 w-5 text-muted-foreground mt-0.5" />
                                <div>
                                    <p className="text-sm text-muted-foreground">Interest Rate</p>
                                    <p className="text-lg font-semibold">{details?.interest ?? 0}%</p>
                                </div>
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

export default LenderDashboard;
