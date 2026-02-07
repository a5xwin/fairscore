import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Loan } from '@/types';
import { Link } from 'react-router-dom';

const MyLoans = () => {
    // Mock data
    const loans: Loan[] = [
        {
            id: 'LN-2023-001',
            borrowerId: '1',
            borrowerName: 'John Borrower',
            amount: 5000,
            tenureMonths: 12,
            interestRate: 5.5,
            status: 'funded',
            appliedDate: '2023-10-15',
        },
        {
            id: 'LN-2024-002',
            borrowerId: '1',
            borrowerName: 'John Borrower',
            amount: 15000,
            tenureMonths: 36,
            interestRate: 6.2,
            status: 'pending',
            appliedDate: '2024-02-01',
        }
    ];

    const getStatusBadge = (status: Loan['status']) => {
        switch (status) {
            case 'approved': return <Badge className="bg-green-500">Approved</Badge>;
            case 'funded': return <Badge className="bg-blue-500">Funded</Badge>;
            case 'rejected': return <Badge variant="destructive">Rejected</Badge>;
            case 'completed': return <Badge variant="secondary">Completed</Badge>;
            default: return <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-200">Pending</Badge>;
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">My Loans</h2>
                <Button asChild>
                    <Link to="/borrower/apply">Apply New Loan</Link>
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Loan History</CardTitle>
                    <CardDescription>View status and details of your loan applications.</CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Loan ID</TableHead>
                                <TableHead>Amount</TableHead>
                                <TableHead>Tenure</TableHead>
                                <TableHead>Applied Date</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead className="text-right">Action</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loans.map((loan) => (
                                <TableRow key={loan.id}>
                                    <TableCell className="font-medium">{loan.id}</TableCell>
                                    <TableCell>${loan.amount.toLocaleString()}</TableCell>
                                    <TableCell>{loan.tenureMonths} months</TableCell>
                                    <TableCell>{new Date(loan.appliedDate).toLocaleDateString()}</TableCell>
                                    <TableCell>{getStatusBadge(loan.status)}</TableCell>
                                    <TableCell className="text-right">
                                        <Button variant="ghost" size="sm" asChild>
                                            <Link to={`/borrower/loans/${loan.id}`}>View</Link>
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

export default MyLoans;
