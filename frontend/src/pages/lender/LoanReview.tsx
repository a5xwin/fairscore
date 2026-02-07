import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Check, X } from 'lucide-react';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';

const LoanReview = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [remarks, setRemarks] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    // Mock data fetch based on ID
    const loanDetails = {
        name: 'John Doe',
        amount: 5000,
        purpose: 'Small Business',
        score: 720,
        income: 55000,
        employment: '3 Years (Software Engineer)',
        dti: '25%',
        risk: 'Low',
        explanation: [
            { factor: 'Payment History', impact: 'High', score: 90 },
            { factor: 'Credit Utilization', impact: 'Medium', score: 75 },
            { factor: 'Length of Credit History', impact: 'Low', score: 60 },
        ]
    };

    const handleAction = async (action: 'approve' | 'reject') => {
        setIsLoading(true);
        // Simulate API
        await new Promise(resolve => setTimeout(resolve, 1500));

        toast.success(`Loan application ${action}d successfully!`);
        setIsLoading(false);
        navigate('/lender/borrowers');
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Review Application #{id}</h2>
                <div className="flex gap-2">
                    <Button variant="destructive" onClick={() => handleAction('reject')} disabled={isLoading}>
                        <X className="mr-2 h-4 w-4" /> Reject
                    </Button>
                    <Button className="bg-green-600 hover:bg-green-700" onClick={() => handleAction('approve')} disabled={isLoading}>
                        <Check className="mr-2 h-4 w-4" /> Approve & Fund
                    </Button>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Applicant Details</CardTitle>
                        <CardDescription>Personal and financial information.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <h4 className="text-sm font-medium text-muted-foreground">Name</h4>
                                <p className="text-lg font-medium">{loanDetails.name}</p>
                            </div>
                            <div>
                                <h4 className="text-sm font-medium text-muted-foreground">Requested Amount</h4>
                                <p className="text-lg font-medium">${loanDetails.amount.toLocaleString()}</p>
                            </div>
                            <div>
                                <h4 className="text-sm font-medium text-muted-foreground">Annual Income</h4>
                                <p className="text-lg font-medium">${loanDetails.income.toLocaleString()}</p>
                            </div>
                            <div>
                                <h4 className="text-sm font-medium text-muted-foreground">Employment</h4>
                                <p className="text-lg font-medium">{loanDetails.employment}</p>
                            </div>
                            <div>
                                <h4 className="text-sm font-medium text-muted-foreground">Purpose</h4>
                                <p className="text-lg font-medium">{loanDetails.purpose}</p>
                            </div>
                            <div>
                                <h4 className="text-sm font-medium text-muted-foreground">Debt-to-Income</h4>
                                <p className="text-lg font-medium">{loanDetails.dti}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>AI Risk Assessment</CardTitle>
                        <CardDescription>FairScore analysis and explainability.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h4 className="text-sm font-medium text-muted-foreground">Credit Score</h4>
                                <p className="text-3xl font-bold text-primary">{loanDetails.score}</p>
                            </div>
                            <div className="text-right">
                                <h4 className="text-sm font-medium text-muted-foreground">Risk Level</h4>
                                <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-green-500 text-white shadow hover:bg-green-500/80">
                                    {loanDetails.risk}
                                </span>
                            </div>
                        </div>
                        <Separator />
                        <div className="space-y-4">
                            <h4 className="text-sm font-medium">Explainability Factors (SHAP/LIME)</h4>
                            {loanDetails.explanation.map((item, index) => (
                                <div key={index} className="space-y-1">
                                    <div className="flex justify-between text-sm">
                                        <span>{item.factor}</span>
                                        <span className="text-muted-foreground">{item.score}/100</span>
                                    </div>
                                    <Progress value={item.score} className="h-2" />
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Lender Remarks</CardTitle>
                </CardHeader>
                <CardContent>
                    <Textarea
                        placeholder="Add any notes or reasons for approval/rejection..."
                        className="min-h-[100px]"
                        value={remarks}
                        onChange={(e) => setRemarks(e.target.value)}
                    />
                </CardContent>
            </Card>
        </div>
    );
};

export default LoanReview;
