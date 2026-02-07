import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useState } from 'react';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

const CreditCheck = () => {
    const [income, setIncome] = useState('');
    const [employment, setEmployment] = useState('');
    const [score, setScore] = useState<number | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const calculateScore = async () => {
        setIsLoading(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Mock score generation
        const mockScore = Math.floor(Math.random() * (850 - 550 + 1)) + 550;
        setScore(mockScore);
        setIsLoading(false);
    };

    return (
        <div className="space-y-6">
            <h2 className="text-3xl font-bold tracking-tight">AI Credit Check</h2>
            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Enter Financial Details</CardTitle>
                        <CardDescription>Our AI model will analyze this to generate a fair score.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="income">Annual Income ($)</Label>
                            <Input
                                id="income"
                                type="number"
                                placeholder="e.g. 50000"
                                value={income}
                                onChange={(e) => setIncome(e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="employment">Years of Employment</Label>
                            <Input
                                id="employment"
                                type="number"
                                placeholder="e.g. 3"
                                value={employment}
                                onChange={(e) => setEmployment(e.target.value)}
                            />
                        </div>
                    </CardContent>
                    <CardFooter>
                        <Button onClick={calculateScore} disabled={isLoading || !income} className="w-full">
                            {isLoading ? 'Analyzing...' : 'Generate Score'}
                        </Button>
                    </CardFooter>
                </Card>

                {score !== null && (
                    <div className="space-y-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Your FairScore</CardTitle>
                                <CardDescription>Generated using Explainable AI</CardDescription>
                            </CardHeader>
                            <CardContent className="flex flex-col items-center justify-center py-6">
                                <div className="relative flex items-center justify-center">
                                    <div className="text-6xl font-bold text-primary">{score}</div>
                                </div>
                                <Progress value={(score / 850) * 100} className="w-full mt-4 h-3" />
                                <div className="flex justify-between w-full text-xs text-muted-foreground mt-2">
                                    <span>Poor (300)</span>
                                    <span>Excellent (850)</span>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>Why this score?</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <Alert>
                                    <CheckCircle2 className="h-4 w-4" />
                                    <AlertTitle>Positive Factors</AlertTitle>
                                    <AlertDescription>
                                        <ul className="list-disc pl-4 mt-2 space-y-1">
                                            <li>Consistent income history (+35 points)</li>
                                            <li>Low debt-to-income ratio (+20 points)</li>
                                        </ul>
                                    </AlertDescription>
                                </Alert>
                                <Alert variant="destructive">
                                    <AlertCircle className="h-4 w-4" />
                                    <AlertTitle>Areas for Improvement</AlertTitle>
                                    <AlertDescription>
                                        <ul className="list-disc pl-4 mt-2 space-y-1">
                                            <li>Short credit history duration (-15 points)</li>
                                        </ul>
                                    </AlertDescription>
                                </Alert>
                            </CardContent>
                        </Card>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CreditCheck;
