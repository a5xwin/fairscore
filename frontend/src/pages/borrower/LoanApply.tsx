import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { useState } from 'react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const LoanApply = () => {
    const [amount, setAmount] = useState([5000]);
    const [tenure, setTenure] = useState('12');
    const [purpose, setPurpose] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));

        toast.success('Loan application submitted successfully!');
        setIsLoading(false);
        navigate('/borrower/loans');
    };

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <h2 className="text-3xl font-bold tracking-tight">Apply for a Loan</h2>
            <Card>
                <CardHeader>
                    <CardTitle>Loan Details</CardTitle>
                    <CardDescription>Customize your loan request.</CardDescription>
                </CardHeader>
                <form onSubmit={handleSubmit}>
                    <CardContent className="space-y-6">
                        <div className="space-y-4">
                            <div className="flex justify-between">
                                <Label htmlFor="amount">Loan Amount</Label>
                                <span className="text-sm font-medium text-primary">${amount[0].toLocaleString()}</span>
                            </div>
                            <Slider
                                id="amount"
                                min={1000}
                                max={50000}
                                step={500}
                                value={amount}
                                onValueChange={setAmount}
                            />
                            <div className="flex justify-between text-xs text-muted-foreground">
                                <span>$1,000</span>
                                <span>$50,000</span>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="tenure">Tenure (Months)</Label>
                            <Select value={tenure} onValueChange={setTenure}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select tenure" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="6">6 Months</SelectItem>
                                    <SelectItem value="12">12 Months</SelectItem>
                                    <SelectItem value="24">24 Months</SelectItem>
                                    <SelectItem value="36">36 Months</SelectItem>
                                    <SelectItem value="48">48 Months</SelectItem>
                                    <SelectItem value="60">60 Months</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="purpose">Purpose of Loan</Label>
                            <Select value={purpose} onValueChange={setPurpose}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select purpose" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="personal">Personal</SelectItem>
                                    <SelectItem value="business">Business</SelectItem>
                                    <SelectItem value="education">Education</SelectItem>
                                    <SelectItem value="home">Home Improvement</SelectItem>
                                    <SelectItem value="other">Other</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                    <CardFooter>
                        <Button type="submit" className="w-full" disabled={isLoading}>
                            {isLoading ? 'Submitting...' : 'Submit Application'}
                        </Button>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
};

export default LoanApply;
