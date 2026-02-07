import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ShieldCheck, TrendingUp, Users } from 'lucide-react';
import { Link } from 'react-router-dom';

const Landing = () => {
    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b">
                <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center">
                            <span className="font-bold text-primary">FS</span>
                        </div>
                        <span className="text-xl font-bold tracking-tight">FairScore</span>
                    </div>
                    <div className="flex gap-4">
                        <Button variant="ghost" asChild>
                            <Link to="/login">Login</Link>
                        </Button>
                        <Button asChild>
                            <Link to="/register">Get Started</Link>
                        </Button>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="py-24 lg:py-32">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
                        Fair and Transparent <span className="text-primary">Credit Scoring</span>
                    </h1>
                    <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
                        Leverage AI to get a fair assessment of your creditworthiness. We use explainable AI to show you exactly why you got your score.
                    </p>
                    <div className="mt-10 flex justify-center gap-4">
                        <Button size="lg" asChild>
                            <Link to="/register">Apply for Loan</Link>
                        </Button>
                        <Button size="lg" variant="outline" asChild>
                            <Link to="/login">I'm a Lender</Link>
                        </Button>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="bg-muted/50 py-24">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid gap-12 sm:grid-cols-2 lg:grid-cols-3">
                        <div className="flex flex-col items-center text-center">
                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                                <ShieldCheck className="h-6 w-6" />
                            </div>
                            <h3 className="mt-6 text-xl font-bold">AI-Powered Analysis</h3>
                            <p className="mt-2 text-muted-foreground">
                                Our advanced algorithms analyze diverse data points to give you a fair score.
                            </p>
                        </div>
                        <div className="flex flex-col items-center text-center">
                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                                <TrendingUp className="h-6 w-6" />
                            </div>
                            <h3 className="mt-6 text-xl font-bold">Explainable Results</h3>
                            <p className="mt-2 text-muted-foreground">
                                Understand the factors influencing your score with detailed SHAP/LIME explanations.
                            </p>
                        </div>
                        <div className="flex flex-col items-center text-center">
                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                                <Users className="h-6 w-6" />
                            </div>
                            <h3 className="mt-6 text-xl font-bold">Peer-to-Peer Lending</h3>
                            <p className="mt-2 text-muted-foreground">
                                Connect directly with lenders who are looking for borrowers like you.
                            </p>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
};

export default Landing;
