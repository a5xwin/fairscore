import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { authService } from '@/services/authService';

const Register = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState<'borrower' | 'lender'>('borrower');
    const { login } = useAuth();
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (password.length < 7) {
        toast.error("Password must be at least 7 characters long");
        return;
    }
        setIsLoading(true);

        try {
            const data = await authService.register({ name, email, password, role });

            const user = {
                id: data.userid,
                name: data.name,
                email: data.email,
                role: data.role,
            };

            login(user, data.token ?? '');

            // Borrowers go to onboarding first; lenders go to lender onboarding
            if (data.role === 'borrower') {
                navigate('/borrower/onboarding');
            } else {
                navigate('/lender/onboarding');
            }
            toast.success(`Welcome to FairScore, ${data.name}!`);

        } catch (error: any) {
            const msg = error?.response?.data?.detail || 'Registration failed. Try again.';
            toast.error(msg);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
            <Card className="w-full max-w-sm">
                <CardHeader className="space-y-1">
                    <CardTitle className="text-2xl font-bold">Create an account</CardTitle>
                    <CardDescription>
                        Enter your email below to create your account
                    </CardDescription>
                </CardHeader>
                <form onSubmit={handleSubmit}>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Full Name</Label>
                            <Input
                                id="name"
                                placeholder="John Doe"
                                required
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="m@example.com"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password">Password</Label>
                            <Input
                                id="password"
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>I want to...</Label>
                            <RadioGroup defaultValue="borrower" value={role} onValueChange={(v) => setRole(v as 'borrower' | 'lender')}>
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="borrower" id="borrower" />
                                    <Label htmlFor="borrower">Borrow Money</Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="lender" id="lender" />
                                    <Label htmlFor="lender">Lend Money</Label>
                                </div>
                            </RadioGroup>
                        </div>
                    </CardContent>
                    <CardFooter className="flex flex-col gap-4">
                        <Button className="w-full" type="submit" disabled={isLoading}>
                            {isLoading ? "Creating account..." : "Create account"}
                        </Button>
                        <div className="text-center text-sm">
                            Already have an account? <Link to="/login" className="underline hover:text-primary">Login</Link>
                        </div>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
};

export default Register;
