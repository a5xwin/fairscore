import { Minus, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

interface StepperProps {
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  label: string;
}

const Stepper = ({ value, onChange, min, max, label }: StepperProps) => {
  const handleDecrement = () => {
    if (value > min) {
      onChange(value - 1);
    }
  };

  const handleIncrement = () => {
    if (value < max) {
      onChange(value + 1);
    }
  };

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-muted-foreground">{label}</label>
      <div className="flex items-center gap-4">
        <Button
          type="button"
          variant="outline"
          size="icon"
          onClick={handleDecrement}
          disabled={value <= min}
          className="h-10 w-10 rounded-lg border-border/50 bg-secondary/50 hover:bg-secondary disabled:opacity-30"
        >
          <Minus className="h-4 w-4" />
        </Button>
        <div className="w-16 text-center">
          <span className="text-2xl font-semibold text-foreground">{value}</span>
        </div>
        <Button
          type="button"
          variant="outline"
          size="icon"
          onClick={handleIncrement}
          disabled={value >= max}
          className="h-10 w-10 rounded-lg border-border/50 bg-secondary/50 hover:bg-secondary disabled:opacity-30"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

export default Stepper;
