import { Shield } from "lucide-react";

const Header = () => {
  return (
    <header className="py-6">
      <div className="flex items-center justify-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center glow-effect">
          <Shield className="h-5 w-5 text-primary-foreground" />
        </div>
        <h1 className="text-2xl md:text-3xl font-bold">
          <span className="text-foreground">Fair</span>
          <span className="gradient-text">Score</span>
        </h1>
      </div>
      <p className="text-center mt-3 text-muted-foreground text-sm md:text-base max-w-md mx-auto">
        Get a fair assessment of your loan eligibility with our transparent scoring system
      </p>
    </header>
  );
};

export default Header;
