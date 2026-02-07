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
import BorrowerDashboard from "./pages/borrower/BorrowerDashboard";
import CreditCheck from "./pages/borrower/CreditCheck";
import LoanApply from "./pages/borrower/LoanApply";
import MyLoans from "./pages/borrower/MyLoans";
import Documents from "./pages/borrower/Documents";
import Profile from "./pages/borrower/Profile";

// Lender Pages
import LenderDashboard from "./pages/lender/LenderDashboard";
import BorrowerList from "./pages/lender/BorrowerList";
import LoanReview from "./pages/lender/LoanReview";

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
              <Route path="/borrower" element={<Layout><Navigate to="/borrower/dashboard" replace /></Layout>} />
              <Route path="/borrower/*" element={
                <Layout>
                  <Routes>
                    <Route path="dashboard" element={<BorrowerDashboard />} />
                    <Route path="credit-check" element={<CreditCheck />} />
                    <Route path="apply" element={<LoanApply />} />
                    <Route path="loans" element={<MyLoans />} />
                    <Route path="documents" element={<Documents />} />
                    <Route path="settings" element={<Profile />} />
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                </Layout>
              } />
            </Route>

            {/* Lender Routes */}
            <Route element={<ProtectedRoute allowedRoles={['lender']} />}>
              <Route path="/lender" element={<Layout><Navigate to="/lender/dashboard" replace /></Layout>} />
              <Route path="/lender/*" element={
                <Layout>
                  <Routes>
                    <Route path="dashboard" element={<LenderDashboard />} />
                    <Route path="borrowers" element={<BorrowerList />} />
                    <Route path="reviews" element={<BorrowerList />} />
                    <Route path="reviews/:id" element={<LoanReview />} />
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
