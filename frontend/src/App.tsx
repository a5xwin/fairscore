import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/layout/ProtectedRoute";
import Layout from "./components/layout/Layout";

// Public Pages
import Landing from "./pages/public/Landing";
import Login from "./pages/public/Login";
import Register from "./pages/public/Register";
import NotFound from "./pages/NotFound";

// Borrower Pages
import BorrowerOnboarding from "./pages/borrower/BorrowerOnboarding";
import BorrowerDashboard from "./pages/borrower/BorrowerDashboard";
import LoanDetails from "./pages/borrower/LoanDetails";
import LoanApply from "./pages/borrower/LoanApply";
import Approvals from "./pages/borrower/Approvals";

// Lender Pages
import LenderOnboarding from "./pages/lender/LenderOnboarding";
import LenderDashboard from "./pages/lender/LenderDashboard";
import LoanRequests from "./pages/lender/LoanRequests";
import ApprovalList from "./pages/lender/ApprovalList";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <AuthProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Borrower Routes */}
            <Route element={<ProtectedRoute allowedRoles={['borrower']} />}>
              <Route path="/borrower/onboarding" element={<BorrowerOnboarding />} />
              <Route path="/borrower" element={<Layout><Navigate to="/borrower/dashboard" replace /></Layout>} />
              <Route path="/borrower/*" element={
                <Layout>
                  <Routes>
                    <Route path="dashboard" element={<BorrowerDashboard />} />
                    <Route path="loan-details" element={<LoanDetails />} />
                    <Route path="apply" element={<LoanApply />} />
                    <Route path="approvals" element={<Approvals />} />
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                </Layout>
              } />
            </Route>

            {/* Lender Routes */}
            <Route element={<ProtectedRoute allowedRoles={['lender']} />}>
              <Route path="/lender/onboarding" element={<LenderOnboarding />} />
              <Route path="/lender" element={<Layout><Navigate to="/lender/dashboard" replace /></Layout>} />
              <Route path="/lender/*" element={
                <Layout>
                  <Routes>
                    <Route path="dashboard" element={<LenderDashboard />} />
                    <Route path="loan-requests" element={<LoanRequests />} />
                    <Route path="approval-list" element={<ApprovalList />} />
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                </Layout>
              } />
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
