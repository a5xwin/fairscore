import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { authService } from '@/services/authService';
import { Landmark } from 'lucide-react';

const LenderOnboarding = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [isSubmitting, setIsSubmitting] = useState(false);

    const [type, setType] = useState('');
    const [capacity, setCapacity] = useState('');
    const [loanAmountFrom, setLoanAmountFrom] = useState('');
    const [loanAmountTo, setLoanAmountTo] = useState('');
    const [interest, setInterest] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!type || !capacity || !loanAmountFrom || !loanAmountTo || !interest) {
            toast.error('Please fill all fields.');
            return;
        }
        if (Number(loanAmountFrom) >= Number(loanAmountTo)) {
            toast.error('Loan range "From" must be less than "To".');
            return;
        }

        setIsSubmitting(true);
        try {
            await authService.submitLenderDetails({
                lenderId: user?.id ?? '',
                type,
                capacity: Number(capacity),
                loanAmountFrom: Number(loanAmountFrom),
                loanAmountTo: Number(loanAmountTo),
                interest: Number(interest),
            });
            localStorage.setItem('onboarded', 'true');
            toast.success('Lender profile setup complete!');
            navigate('/lender/dashboard');
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string } } };
            toast.error(e?.response?.data?.detail || 'Failed to submit details.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-muted/40 flex items-center justify-center p-4">
            <Card className="w-full max-w-lg">
                <CardHeader className="text-center space-y-2">
                    <div className="mx-auto h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                        <Landmark className="h-6 w-6 text-primary" />
                    </div>
                    <CardTitle className="text-2xl font-bold">Welcome, {user?.name}!</CardTitle>
                    <CardDescription>Set up your lender profile to start reviewing borrowers.</CardDescription>
                </CardHeader>

                <form onSubmit={handleSubmit}>
                    <CardContent className="space-y-5">
                        {/* Lender Type */}
                        <div className="space-y-2">
                            <Label>Lender Type</Label>
                            <RadioGroup value={type} onValueChange={setType} className="flex gap-4">
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="individual" id="individual" />
                                    <Label htmlFor="individual">Individual</Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="financial_institution" id="institution" />
                                    <Label htmlFor="institution">Financial Institution</Label>
                                </div>
                            </RadioGroup>
                        </div>

                        {/* Lending Capacity */}
                        <div className="space-y-2">
                            <Label htmlFor="capacity">Lending Capacity (₹)</Label>
                            <Input
                                id="capacity"
                                type="number"
                                placeholder="e.g. 5000000"
                                min={0}
                                required
                                value={capacity}
                                onChange={(e) => setCapacity(e.target.value)}
                            />
                        </div>

                        {/* Loan Range */}
                        <div className="space-y-2">
                            <Label>Loan Range (₹)</Label>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <Label className="text-xs text-muted-foreground">From</Label>
                                    <Input
                                        type="number"
                                        placeholder="Min amount"
                                        min={0}
                                        required
                                        value={loanAmountFrom}
                                        onChange={(e) => setLoanAmountFrom(e.target.value)}
                                    />
                                </div>
                                <div className="space-y-1">
                                    <Label className="text-xs text-muted-foreground">To</Label>
                                    <Input
                                        type="number"
                                        placeholder="Max amount"
                                        min={0}
                                        required
                                        value={loanAmountTo}
                                        onChange={(e) => setLoanAmountTo(e.target.value)}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Interest Rate */}
                        <div className="space-y-2">
                            <Label htmlFor="interest">Interest Rate (%)</Label>
                            <Input
                                id="interest"
                                type="number"
                                step="0.01"
                                placeholder="e.g. 8.5"
                                min={0}
                                max={100}
                                required
                                value={interest}
                                onChange={(e) => setInterest(e.target.value)}
                            />
                        </div>
                    </CardContent>

                    <CardFooter>
                        <Button className="w-full" type="submit" disabled={isSubmitting}>
                            {isSubmitting ? 'Setting up...' : 'Complete Setup'}
                        </Button>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
};

export default LenderOnboarding;
