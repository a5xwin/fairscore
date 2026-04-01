import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
    LayoutDashboard,
    CreditCard,
    LogOut,
    Settings,
    Menu,
    CheckCircle,
    Send,
    ClipboardList
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';

const Layout = ({ children }: { children: React.ReactNode }) => {
    const { user, logout } = useAuth();
    const location = useLocation();
    const [isMobileOpen, setIsMobileOpen] = React.useState(false);

    if (!user) return null;

    const borrowerLinks = [
        { title: 'Dashboard', href: '/borrower/dashboard', icon: LayoutDashboard },
        { title: 'Loan Details', href: '/borrower/loan-details', icon: CreditCard },
        { title: 'Apply Loan', href: '/borrower/apply', icon: Send },
        { title: 'Approvals', href: '/borrower/approvals', icon: CheckCircle },
    ];

    const lenderLinks = [
        { title: 'Dashboard', href: '/lender/dashboard', icon: LayoutDashboard },
        { title: 'Loan Requests', href: '/lender/loan-requests', icon: ClipboardList },
        { title: 'Approval List', href: '/lender/approval-list', icon: CheckCircle },
    ];

    const links = user.role === 'borrower' ? borrowerLinks : lenderLinks;

    const SidebarContent = ({ className }: { className?: string }) => (
        <div className={cn("flex h-full min-h-0 flex-col gap-4 py-4", className)}>
            <div className="px-6 flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center">
                    <span className="font-bold text-primary">FS</span>
                </div>
                <span className="text-xl font-bold tracking-tight">FairScore</span>
            </div>
            <div className="mt-6 flex-1 overflow-y-auto px-4">
                <nav className="grid gap-2">
                    {links.map((link) => (
                        <Link
                            key={link.title}
                            to={link.href}
                            onClick={() => setIsMobileOpen(false)}
                            className={cn(
                                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all hover:bg-accent hover:text-accent-foreground",
                                location.pathname === link.href ? "bg-accent/80 text-accent-foreground" : "text-muted-foreground"
                            )}
                        >
                            <link.icon className="h-4 w-4" />
                            {link.title}
                        </Link>
                    ))}
                </nav>
            </div>
            <div className="px-4 mt-auto">
                {user.role === 'borrower' && (
                    <Link
                        to="/borrower/profile"
                        onClick={() => setIsMobileOpen(false)}
                        className={cn(
                            "mb-2 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all hover:bg-accent hover:text-accent-foreground",
                            location.pathname === '/borrower/profile' ? "bg-accent/80 text-accent-foreground" : "text-muted-foreground"
                        )}
                    >
                        <Settings className="h-4 w-4" />
                        Profile
                    </Link>
                )}
                <Button variant="ghost" className="w-full justify-start gap-3 text-muted-foreground hover:text-destructive" onClick={logout}>
                    <LogOut className="h-4 w-4" />
                    Logout
                </Button>
            </div>
        </div>
    );

    return (
        <div className="grid min-h-screen w-full lg:grid-cols-[280px_1fr]">
            <div className="hidden border-r bg-muted/40 lg:sticky lg:top-0 lg:block lg:h-screen">
                <SidebarContent className="h-screen" />
            </div>
            <div className="flex flex-col">
                <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-6 lg:hidden">
                    <Sheet open={isMobileOpen} onOpenChange={setIsMobileOpen}>
                        <SheetTrigger asChild>
                            <Button variant="outline" size="icon" className="shrink-0">
                                <Menu className="h-5 w-5" />
                                <span className="sr-only">Toggle navigation menu</span>
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="left" className="flex flex-col p-0 w-64">
                            <SidebarContent className="h-full" />
                        </SheetContent>
                    </Sheet>
                    <div className="font-semibold">FairScore</div>
                </header>
                <main className="flex-1 p-6 lg:p-8">
                    {children}
                </main>
            </div>
        </div>
    );
};

export default Layout;
