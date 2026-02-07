import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Search } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

const BorrowerList = () => {
    // Mock data
    const borrowers = [
        { id: '1', name: 'John Doe', score: 720, income: 55000, requested: 5000, risk: 'Low' },
        { id: '2', name: 'Jane Smith', score: 650, income: 42000, requested: 10000, risk: 'Medium' },
        { id: '3', name: 'Bob Johnson', score: 580, income: 38000, requested: 2000, risk: 'High' },
        { id: '4', name: 'Alice Williams', score: 780, income: 85000, requested: 25000, risk: 'Very Low' },
    ];

    const [searchTerm, setSearchTerm] = useState('');

    const filteredBorrowers = borrowers.filter(b =>
        b.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getRiskBadge = (risk: string) => {
        switch (risk) {
            case 'Very Low': return <Badge className="bg-green-600">Very Low</Badge>;
            case 'Low': return <Badge className="bg-green-500">Low</Badge>;
            case 'Medium': return <Badge className="bg-yellow-500">Medium</Badge>;
            case 'High': return <Badge className="bg-red-500">High</Badge>;
            default: return <Badge variant="outline">Unknown</Badge>;
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Borrower Marketplace</h2>
            </div>

            <div className="flex items-center space-x-2">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search borrowers..."
                        className="pl-8"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Active Loan Requests</CardTitle>
                    <CardDescription>Review and fund borrower applications.</CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Borrower Name</TableHead>
                                <TableHead>Credit Score</TableHead>
                                <TableHead>Annual Income</TableHead>
                                <TableHead>Requested Amount</TableHead>
                                <TableHead>Risk Level</TableHead>
                                <TableHead className="text-right">Action</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredBorrowers.map((borrower) => (
                                <TableRow key={borrower.id}>
                                    <TableCell className="font-medium">{borrower.name}</TableCell>
                                    <TableCell>{borrower.score}</TableCell>
                                    <TableCell>${borrower.income.toLocaleString()}</TableCell>
                                    <TableCell>${borrower.requested.toLocaleString()}</TableCell>
                                    <TableCell>{getRiskBadge(borrower.risk)}</TableCell>
                                    <TableCell className="text-right">
                                        <Button size="sm" asChild>
                                            <Link to={`/lender/reviews/${borrower.id}`}>Review</Link>
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
};

export default BorrowerList;
