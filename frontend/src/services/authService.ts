import api from './api';
import { User } from '../types';

export const authService = {
    login: async (credentials: any) => {
        // const response = await api.post('/borrower/login', credentials);
        // return response.data;
        // Mock for now is handled in component, but this is structure:
        return Promise.resolve({ user: { id: '1', name: 'Test', role: 'borrower' }, token: 'abc' });
    },
    register: async (data: any) => {
        // const response = await api.post('/borrower/register', data);
        // return response.data;
        return Promise.resolve({ user: { id: '2', name: 'Test', role: 'borrower' }, token: 'abc' });
    },
    getProfile: async () => {
        const response = await api.get('/borrower/profile');
        return response.data;
    },
    updateProfile: async (data: Partial<User>) => {
        const response = await api.patch('/borrower/profile/update', data);
        return response.data;
    }
};
