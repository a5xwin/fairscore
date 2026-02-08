import api from './api';
import { User } from '../types';

export interface RegisterPayload {
    name: string;
    email: string;
    password: string;
    role: 'borrower' | 'lender';
}

export interface LoginPayload {
    email: string;
    password: string;
}

export interface AuthResponse {
    userid: string;
    name: string;
    email: string;
    role: 'borrower' | 'lender';
    token?: string;
}

export interface BorrowerDetailsPayload {
    userid: string;
    dob: string;
    gender: string;
    state: string;
    city: string;
    phone: string;
    empProfile: string;
    occupation: string;
    income: number;
    creditHistoryYr: number;
    creditHistoryMon: number;
    loanNo: number;
    assetValue: number;
    loanAmount: number;
    loanTenureYr: number;
    loanTenureMon: number;
    purpose: string;
}

export interface CreditInfo {
    creditScore: number;
    Risk: string;
    creditLine: number;
}

export interface LoanInfo {
    loanAmount: number;
    loanTenureYr: number;
    loanTenureMon: number;
    purpose: string;
}

export interface LoanUpdatePayload {
    userid: string;
    loanAmount: number;
    loanTenureYr: number;
    loanTenureMon: number;
    purpose: string;
}

export interface LenderInfo {
    lenderid: string;
    name: string;
    type: string;
    loanAmountFrom: number;
    loanAmountTo: number;
    Interest: number;
}

export interface ApprovedLender {
    lenderId: string;
    Name: string;
    type: string;
    capacity: number;
    loanAmountFrom: number;
    loanAmountTo: number;
    interest: number;
}

// --- Lender interfaces ---

export interface LenderDetailsPayload {
    lenderId: string;
    type: string;
    capacity: number;
    loanAmountFrom: number;
    loanAmountTo: number;
    interest: number;
}

export interface LenderDetails {
    name: string;
    type: string;
    capacity: number;
    loanAmountFrom: number;
    loanAmountTo: number;
    interest: number;
}

export interface LenderDetailsUpdatePayload {
    lenderID: string;
    capacity: number;
    loanAmountFrom: number;
    loanAmountTo: number;
    interest: number;
}

export interface LoanRequestBorrower {
    userid: string;
    name: string;
    creditScore: number;
    risk: string;
    income: number;
    loanAmount: number;
    loanTenureYr: number;
    loanTenureMon: number;
}

export interface ApprovedBorrower {
    userid: string;
    name: string;
    email: string;
    age: number;
    state: string;
    city: string;
    occupation: string;
    gender: string;
    creditScore: number;
    risk: string;
    income: number;
    loanNo: number;
    ltvRatio: number;
    loanAmount: number;
    loanTenureYr: number;
    loanTenureMon: number;
}

export const authService = {
    register: async (data: RegisterPayload): Promise<AuthResponse> => {
        const response = await api.post('/register', data);
        return response.data;
    },
    login: async (credentials: LoginPayload): Promise<AuthResponse> => {
        const response = await api.post('/login', credentials);
        return response.data;
    },
    submitBorrowerDetails: async (data: BorrowerDetailsPayload): Promise<Record<string, unknown>> => {
        const response = await api.post('/borrower/details', data);
        return response.data;
    },

    // Borrower Dashboard
    getCreditInfo: async (userid: string): Promise<CreditInfo> => {
        const response = await api.get('/borrower/credit-info', { params: { userid } });
        return response.data;
    },

    // Loan Details
    getLoanInfo: async (userid: string): Promise<LoanInfo> => {
        const response = await api.get('/borrower/loan-info', { params: { userid } });
        return response.data;
    },
    updateLoanInfo: async (data: LoanUpdatePayload): Promise<{ status: string }> => {
        const response = await api.put('/borrower/loan-update', data);
        return response.data;
    },

    // Apply Loan – browse lenders
    getLenderInfo: async (userid: string): Promise<LenderInfo[]> => {
        const response = await api.get('/borrower/lender-info', { params: { userid } });
        return response.data;
    },
    applyToLender: async (userid: string, lenderid: string): Promise<{ status: string }> => {
        const response = await api.post('/borrower/apply', { userid, lenderid });
        return response.data;
    },

    // Approvals
    getApprovedLenders: async (userid: string): Promise<ApprovedLender[]> => {
        const response = await api.get('/borrower/approved-lenders', { params: { userid } });
        return response.data;
    },

    getProfile: async () => {
        const response = await api.get('/borrower/profile');
        return response.data;
    },
    updateProfile: async (data: Partial<User>) => {
        const response = await api.patch('/borrower/profile/update', data);
        return response.data;
    },

    // ===================== LENDER =====================

    // Lender onboarding
    submitLenderDetails: async (data: LenderDetailsPayload): Promise<{ status: string }> => {
        const response = await api.post('/lender/details', data);
        return response.data;
    },

    // Lender dashboard – get & update details
    getLenderDetails: async (lenderId: string): Promise<LenderDetails> => {
        const response = await api.get('/lender/details', { params: { lenderId } });
        return response.data;
    },
    updateLenderDetails: async (data: LenderDetailsUpdatePayload): Promise<{ status: string }> => {
        const response = await api.put('/lender/details', data);
        return response.data;
    },

    // Loan requests
    getLoanRequests: async (lenderID: string): Promise<LoanRequestBorrower[]> => {
        const response = await api.get('/lender/loan-requests', { params: { lenderID } });
        return response.data;
    },
    approveBorrower: async (lenderId: string, userId: string): Promise<{ status: string }> => {
        const response = await api.post('/lender/approve', { lenderId, userId });
        return response.data;
    },
    skipBorrower: async (lenderId: string, userid: string): Promise<{ status: string }> => {
        const response = await api.post('/lender/skip', { lenderId, userid });
        return response.data;
    },

    // Approved borrowers
    getApprovedBorrowers: async (lenderId: string): Promise<ApprovedBorrower[]> => {
        const response = await api.get('/lender/approved-borrowers', { params: { lenderId } });
        return response.data;
    },
};
