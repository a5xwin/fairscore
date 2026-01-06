import { Slider } from "@/components/ui/slider";

interface SliderInputProps {
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  label: string;
  formatValue?: (value: number) => string;
}

const SliderInput = ({ 
  value, 
  onChange, 
  min, 
  max, 
  step = 1, 
  label, 
  formatValue 
}: SliderInputProps) => {
  const displayValue = formatValue ? formatValue(value) : value.toString();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-muted-foreground">{label}</label>
        <span className="text-lg font-semibold text-primary">{displayValue}</span>
      </div>
      <Slider
        value={[value]}
        onValueChange={(vals) => onChange(vals[0])}
        min={min}
        max={max}
        step={step}
        className="w-full"
      />
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{formatValue ? formatValue(min) : min}</span>
        <span>{formatValue ? formatValue(max) : max}</span>
      </div>
    </div>
  );
};

export default SliderInput;
