export type UserRole = 'borrower' | 'lender' | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar?: string;
}

export interface Loan {
  id: string;
  borrowerId: string;
  borrowerName: string;
  amount: number;
  tenureMonths: number;
  interestRate: number;
  status: 'pending' | 'approved' | 'rejected' | 'funded' | 'completed';
  appliedDate: string;
  creditScore?: number;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
}
