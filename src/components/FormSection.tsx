import { ReactNode } from "react";

interface FormSectionProps {
  title: string;
  description?: string;
  icon: ReactNode;
  children: ReactNode;
  step: number;
}

const FormSection = ({ title, description, icon, children, step }: FormSectionProps) => {
  return (
    <div className="glass-card p-6 md:p-8 animate-slide-up" style={{ animationDelay: `${step * 100}ms` }}>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
          {icon}
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">{title}</h2>
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
        </div>
      </div>
      <div className="grid gap-6">
        {children}
      </div>
    </div>
  );
};

export default FormSection;
