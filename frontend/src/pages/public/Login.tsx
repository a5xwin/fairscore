import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'sonner';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        // Mock login logic
        try {
            await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API delay

            // This is where you'd call your actual API
            if (email === 'borrower@test.com' && password === 'password') {
                login({
                    id: '1',
                    name: 'John Borrower',
                    email: 'borrower@test.com',
                    role: 'borrower'
                }, 'mock-jwt-token-borrower');
                navigate('/borrower/dashboard');
                toast.success('Welcome back, John!');
            } else if (email === 'lender@test.com' && password === 'password') {
                login({
                    id: '2',
                    name: 'Jane Lender',
                    email: 'lender@test.com',
                    role: 'lender'
                }, 'mock-jwt-token-lender');
                navigate('/lender/dashboard');
                toast.success('Welcome back, Jane!');
            } else {
                toast.error('Invalid credentials. specific test emails in code.');
            }
        } catch (error) {
            toast.error('Something went wrong');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
            <Card className="w-full max-w-sm">
                <CardHeader className="space-y-1">
                    <CardTitle className="text-2xl font-bold">Login to FairScore</CardTitle>
                    <CardDescription>
                        Enter your email and password to access your account
                    </CardDescription>
                </CardHeader>
                <form onSubmit={handleSubmit}>
                    <CardContent className="space-y-4">
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
                        <div className="text-sm text-muted-foreground mt-2">
                            <p>Test Borrower: borrower@test.com / password</p>
                            <p>Test Lender: lender@test.com / password</p>
                        </div>
                    </CardContent>
                    <CardFooter className="flex flex-col gap-4">
                        <Button className="w-full" type="submit" disabled={isLoading}>
                            {isLoading ? "Signing in..." : "Sign In"}
                        </Button>
                        <div className="text-center text-sm">
                            Don't have an account? <Link to="/register" className="underline hover:text-primary">Register</Link>
                        </div>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
};

export default Login;
