import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
    ShieldCheck,
    TrendingUp,
    Users,
    ArrowRight,
    CheckCircle,
    Zap,
    BarChart3,
    Lock,
    Globe,
    Star,
    ChevronRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';

const Landing = () => {
    return (
        <div className="min-h-screen bg-background overflow-x-hidden">
            {/* Header */}
            <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-md">
                <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center gap-2">
                        <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center shadow-sm">
                            <span className="font-bold text-primary-foreground text-sm">FS</span>
                        </div>
                        <span className="text-xl font-bold tracking-tight">FairScore</span>
                    </div>
                    <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
                        <a href="#features" className="hover:text-foreground transition-colors">Features</a>
                        <a href="#how-it-works" className="hover:text-foreground transition-colors">How It Works</a>
                        <a href="#who" className="hover:text-foreground transition-colors">Who It's For</a>
                    </nav>
                    <div className="flex gap-3">
                        <Button variant="ghost" size="sm" asChild>
                            <Link to="/login">Login</Link>
                        </Button>
                        <Button size="sm" asChild>
                            <Link to="/register">Get Started</Link>
                        </Button>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="relative py-24 lg:py-36">
                {/* Background decoration */}
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-primary/5 rounded-full blur-3xl" />
                    <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-primary/3 rounded-full blur-3xl" />
                </div>

                <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <Badge variant="outline" className="mb-6 px-4 py-1.5 text-sm font-medium border-primary/30 text-primary">
                        <Zap className="h-3.5 w-3.5 mr-1.5" />
                        AI-Powered Credit Assessment
                    </Badge>

                    <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl max-w-4xl mx-auto leading-[1.1]">
                        Fair and Transparent{' '}
                        <span className="bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
                            Credit Scoring
                        </span>{' '}
                        for Everyone
                    </h1>

                    <p className="mx-auto mt-6 max-w-2xl text-lg sm:text-xl text-muted-foreground leading-relaxed">
                        Get a fair assessment of your creditworthiness using explainable AI.
                        Connect directly with lenders and access loans that match your profile.
                    </p>

                    <div className="mt-10 flex flex-col sm:flex-row justify-center gap-4">
                        <Button size="lg" className="text-base px-8 h-12 shadow-lg shadow-primary/20" asChild>
                            <Link to="/register">
                                Apply for a Loan <ArrowRight className="ml-2 h-4 w-4" />
                            </Link>
                        </Button>
                        <Button size="lg" variant="outline" className="text-base px-8 h-12" asChild>
                            <Link to="/register">I'm a Lender</Link>
                        </Button>
                    </div>
                </div>
            </section>

            {/* Stats Section */}
            <section className="border-y bg-muted/30">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
                        {[
                            { value: '50K+', label: 'Credit Assessments' },
                            { value: '95%', label: 'Accuracy Rate' },
                            { value: '₹200Cr+', label: 'Loans Facilitated' },
                            { value: '4.8/5', label: 'User Rating' },
                        ].map((stat) => (
                            <div key={stat.label}>
                                <div className="text-2xl sm:text-3xl font-bold text-foreground">{stat.value}</div>
                                <div className="mt-1 text-sm text-muted-foreground">{stat.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="py-24">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <Badge variant="outline" className="mb-4 text-xs">FEATURES</Badge>
                        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
                            Why Choose FairScore?
                        </h2>
                        <p className="mt-4 max-w-2xl mx-auto text-muted-foreground text-lg">
                            Our platform combines cutting-edge AI with transparency to create a fairer lending ecosystem.
                        </p>
                    </div>

                    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                        {[
                            {
                                icon: ShieldCheck,
                                title: 'AI-Powered Analysis',
                                description: 'Advanced ensemble models analyse diverse data points — income, credit history, assets — to generate a fair, unbiased credit score.',
                                color: 'text-blue-600 bg-blue-50',
                            },
                            {
                                icon: TrendingUp,
                                title: 'Explainable Results',
                                description: 'Understand exactly why you got your score. SHAP-based explanations break down every factor so nothing feels like a black box.',
                                color: 'text-green-600 bg-green-50',
                            },
                            {
                                icon: Users,
                                title: 'Peer-to-Peer Lending',
                                description: 'Skip the middleman. Connect directly with individual lenders and financial institutions looking for borrowers like you.',
                                color: 'text-purple-600 bg-purple-50',
                            },
                            {
                                icon: Lock,
                                title: 'Secure & Private',
                                description: 'Your data is encrypted end-to-end. We never share personal information without explicit consent.',
                                color: 'text-orange-600 bg-orange-50',
                            },
                            {
                                icon: BarChart3,
                                title: 'Real-Time Scoring',
                                description: 'Get your credit score instantly. No waiting weeks for bureau reports — our AI processes your profile in seconds.',
                                color: 'text-rose-600 bg-rose-50',
                            },
                            {
                                icon: Globe,
                                title: 'Pan-India Coverage',
                                description: 'Available across all states and union territories. Designed for the diverse financial landscape of India.',
                                color: 'text-teal-600 bg-teal-50',
                            },
                        ].map((feature) => (
                            <Card key={feature.title} className="group hover:shadow-lg transition-all duration-300 border-border/50">
                                <CardContent className="pt-6">
                                    <div className={`h-11 w-11 rounded-xl flex items-center justify-center ${feature.color} mb-4`}>
                                        <feature.icon className="h-5 w-5" />
                                    </div>
                                    <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                                    <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            </section>

            {/* How It Works */}
            <section id="how-it-works" className="py-24 bg-muted/30">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <Badge variant="outline" className="mb-4 text-xs">HOW IT WORKS</Badge>
                        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
                            Get Started in Minutes
                        </h2>
                        <p className="mt-4 max-w-2xl mx-auto text-muted-foreground text-lg">
                            A simple, streamlined process from sign-up to getting your loan approved.
                        </p>
                    </div>

                    <div className="grid gap-8 md:grid-cols-4 max-w-5xl mx-auto">
                        {[
                            { step: '01', title: 'Create Account', desc: 'Sign up as a borrower or lender in under a minute.' },
                            { step: '02', title: 'Complete Profile', desc: 'Enter your personal, employment, and financial details.' },
                            { step: '03', title: 'Get Your Score', desc: 'Our AI instantly calculates your credit score and risk level.' },
                            { step: '04', title: 'Connect & Transact', desc: 'Browse lenders, apply for loans, and get approved.' },
                        ].map((item, i) => (
                            <div key={item.step} className="relative text-center">
                                <div className="mx-auto mb-4 h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center">
                                    <span className="text-xl font-bold text-primary">{item.step}</span>
                                </div>
                                <h3 className="font-semibold text-lg mb-2">{item.title}</h3>
                                <p className="text-sm text-muted-foreground">{item.desc}</p>
                                {i < 3 && (
                                    <ChevronRight className="hidden md:block absolute top-7 -right-4 h-5 w-5 text-muted-foreground/40" />
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* For Borrowers / For Lenders */}
            <section id="who" className="py-24">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <Badge variant="outline" className="mb-4 text-xs">WHO IT'S FOR</Badge>
                        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
                            Built for Both Sides
                        </h2>
                    </div>

                    <div className="grid gap-8 md:grid-cols-2 max-w-5xl mx-auto">
                        {/* Borrowers */}
                        <Card className="overflow-hidden border-border/50">
                            <div className="h-2 bg-gradient-to-r from-blue-500 to-blue-400" />
                            <CardContent className="pt-8 pb-8">
                                <h3 className="text-2xl font-bold mb-2">For Borrowers</h3>
                                <p className="text-muted-foreground mb-6">
                                    Get a transparent credit score and access to a marketplace of lenders.
                                </p>
                                <ul className="space-y-3">
                                    {[
                                        'Instant AI credit score with full explainability',
                                        'Browse and compare multiple lenders',
                                        'Track loan applications in real-time',
                                        'Edit your loan details and reapply anytime',
                                        'See exactly which lenders approved you',
                                    ].map((item) => (
                                        <li key={item} className="flex items-start gap-3 text-sm">
                                            <CheckCircle className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
                                            <span>{item}</span>
                                        </li>
                                    ))}
                                </ul>
                                <Button className="mt-8 w-full" asChild>
                                    <Link to="/register">Start as Borrower <ArrowRight className="ml-2 h-4 w-4" /></Link>
                                </Button>
                            </CardContent>
                        </Card>

                        {/* Lenders */}
                        <Card className="overflow-hidden border-border/50">
                            <div className="h-2 bg-gradient-to-r from-green-500 to-green-400" />
                            <CardContent className="pt-8 pb-8">
                                <h3 className="text-2xl font-bold mb-2">For Lenders</h3>
                                <p className="text-muted-foreground mb-6">
                                    Access pre-scored borrower profiles and approve loans confidently.
                                </p>
                                <ul className="space-y-3">
                                    {[
                                        'Review borrowers with AI-generated credit scores',
                                        'See income, risk level, and LTV ratio at a glance',
                                        'Approve or skip requests with one click',
                                        'Manage your lending capacity and interest rates',
                                        'Full approved borrower profiles with contact info',
                                    ].map((item) => (
                                        <li key={item} className="flex items-start gap-3 text-sm">
                                            <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                                            <span>{item}</span>
                                        </li>
                                    ))}
                                </ul>
                                <Button variant="outline" className="mt-8 w-full" asChild>
                                    <Link to="/register">Start as Lender <ArrowRight className="ml-2 h-4 w-4" /></Link>
                                </Button>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </section>

            {/* Testimonials */}
            <section className="py-24 bg-muted/30">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <Badge variant="outline" className="mb-4 text-xs">TESTIMONIALS</Badge>
                        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
                            Trusted by Thousands
                        </h2>
                    </div>

                    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 max-w-5xl mx-auto">
                        {[
                            {
                                name: 'Priya Sharma',
                                role: 'Borrower, Delhi',
                                quote: 'I was denied by banks multiple times. FairScore gave me a transparent score and connected me with a lender who approved my education loan in 24 hours.',
                            },
                            {
                                name: 'Rajesh Patel',
                                role: 'Individual Lender, Ahmedabad',
                                quote: 'The risk assessment is incredibly detailed. I can review credit scores, income, and LTV ratios before approving — it takes the guesswork out of lending.',
                            },
                            {
                                name: 'Ananya Reddy',
                                role: 'Borrower, Hyderabad',
                                quote: 'What I love most is the explainability. I could see exactly which factors affected my score and what I could improve. No other platform does this.',
                            },
                        ].map((testimonial) => (
                            <Card key={testimonial.name} className="border-border/50">
                                <CardContent className="pt-6">
                                    <div className="flex gap-1 mb-4">
                                        {[1, 2, 3, 4, 5].map((s) => (
                                            <Star key={s} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                                        ))}
                                    </div>
                                    <p className="text-sm text-muted-foreground leading-relaxed mb-4">
                                        "{testimonial.quote}"
                                    </p>
                                    <div>
                                        <p className="font-semibold text-sm">{testimonial.name}</p>
                                        <p className="text-xs text-muted-foreground">{testimonial.role}</p>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-24">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="relative rounded-3xl bg-gradient-to-br from-primary to-primary/80 px-8 py-16 sm:px-16 text-center overflow-hidden">
                        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.15),transparent_60%)]" />
                        <div className="relative z-10">
                            <h2 className="text-3xl sm:text-4xl font-bold text-primary-foreground tracking-tight">
                                Ready to Get Your Fair Score?
                            </h2>
                            <p className="mt-4 max-w-xl mx-auto text-primary-foreground/80 text-lg">
                                Join thousands of borrowers and lenders using AI-powered, transparent credit scoring.
                            </p>
                            <div className="mt-8 flex flex-col sm:flex-row justify-center gap-4">
                                <Button size="lg" variant="secondary" className="text-base px-8 h-12 shadow-lg" asChild>
                                    <Link to="/register">
                                        Create Free Account <ArrowRight className="ml-2 h-4 w-4" />
                                    </Link>
                                </Button>
                                <Button size="lg" variant="ghost" className="text-base px-8 h-12 text-primary-foreground border border-primary-foreground/30 hover:bg-primary-foreground/10" asChild>
                                    <Link to="/login">Sign In</Link>
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="border-t py-12 bg-muted/20">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                        <div className="flex items-center gap-2">
                            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center">
                                <span className="font-bold text-primary-foreground text-xs">FS</span>
                            </div>
                            <span className="font-bold">FairScore</span>
                        </div>
                        <div className="flex gap-8 text-sm text-muted-foreground">
                            <a href="#features" className="hover:text-foreground transition-colors">Features</a>
                            <a href="#how-it-works" className="hover:text-foreground transition-colors">How It Works</a>
                            <a href="#who" className="hover:text-foreground transition-colors">Who It's For</a>
                        </div>
                        <p className="text-sm text-muted-foreground">
                            &copy; {new Date().getFullYear()} FairScore. All rights reserved.
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default Landing;
