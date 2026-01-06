import Header from "@/components/Header";
import LoanForm from "@/components/LoanForm";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Background gradient effect */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-primary/3 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 container max-w-3xl mx-auto px-4 py-8 md:py-12">
        <Header />
        
        <main className="mt-8">
          <LoanForm />
        </main>

        <footer className="mt-12 text-center text-sm text-muted-foreground">
          <p>© 2026 FairScore. Your trusted loan eligibility partner.</p>
        </footer>
      </div>
    </div>
  );
};

export default Index;
