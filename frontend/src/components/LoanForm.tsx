import { useState, useMemo } from "react";
import { User, Wallet, CreditCard, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import FormSection from "./FormSection";
import Stepper from "./Stepper";
import SliderInput from "./SliderInput";
import { states, statesWithCities, occupations, employmentProfiles } from "@/data/locationData";
import { useToast } from "@/hooks/use-toast";

interface FormData {
  age: string;
  gender: string;
  state: string;
  city: string;
  employmentProfile: string;
  occupation: string;
  income: string;
  creditHistoryLength: number;
  existingLoans: number;
  loanAmount: number;
  loanTenure: number;
}

const LoanForm = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState<FormData>({
    age: "",
    gender: "",
    state: "",
    city: "",
    employmentProfile: "",
    occupation: "",
    income: "",
    creditHistoryLength: 6,
    existingLoans: 0,
    loanAmount: 50000,
    loanTenure: 24,
  });

  const availableCities = useMemo(() => {
    return formData.state ? statesWithCities[formData.state] || [] : [];
  }, [formData.state]);

  const isOccupationDisabled = formData.employmentProfile === "Student" || formData.employmentProfile === "Unemployed";

  const handleStateChange = (value: string) => {
    setFormData(prev => ({ ...prev, state: value, city: "" }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate age
    const age = parseInt(formData.age);
    if (isNaN(age) || age < 18 || age > 70) {
      toast({
        title: "Invalid Age",
        description: "Age must be between 18 and 70 years.",
        variant: "destructive",
      });
      return;
    }

    // Validate credit history length
    const maxCreditHistoryMonths = (age - 18) * 12;
    if (formData.creditHistoryLength > maxCreditHistoryMonths) {
      toast({
        title: "Invalid Credit History",
        description: `At age ${age}, your maximum credit history can be ${maxCreditHistoryMonths} months (${(maxCreditHistoryMonths / 12).toFixed(1)} years). Please adjust accordingly.`,
        variant: "destructive",
      });
      return;
    }

    // Validate income
    const income = parseFloat(formData.income);
    if (isNaN(income) || income < 0) {
      toast({
        title: "Invalid Income",
        description: "Please enter a valid income amount.",
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "Application Submitted!",
      description: "Your loan application is being processed. We'll get back to you soon.",
    });
    
    console.log("Form submitted:", formData);
  };

  const formatCurrency = (value: number) => `₹${value.toLocaleString("en-IN")}`;
  const formatMonths = (value: number) => `${value} months`;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Profile Information */}
      <FormSection
        title="Profile Information"
        description="Tell us about yourself"
        icon={<User className="h-5 w-5" />}
        step={1}
      >
        <div className="grid md:grid-cols-2 gap-6">
          {/* Age */}
          <div className="space-y-2">
            <Label htmlFor="age" className="text-muted-foreground">Age</Label>
            <Input
              id="age"
              type="number"
              min={18}
              max={70}
              placeholder="Enter your age"
              value={formData.age}
              onChange={(e) => setFormData(prev => ({ ...prev, age: e.target.value }))}
              className="input-field"
              required
            />
            <p className="text-xs text-muted-foreground">Must be between 18-70 years</p>
          </div>

          {/* Gender */}
          <div className="space-y-3">
            <Label className="text-muted-foreground">Gender</Label>
            <RadioGroup
              value={formData.gender}
              onValueChange={(value) => setFormData(prev => ({ ...prev, gender: value }))}
              className="flex gap-4"
              required
            >
              {["Male", "Female", "Other"].map((option) => (
                <div key={option} className="flex items-center space-x-2">
                  <RadioGroupItem 
                    value={option} 
                    id={option}
                    className="border-border text-primary"
                  />
                  <Label htmlFor={option} className="text-foreground cursor-pointer">{option}</Label>
                </div>
              ))}
            </RadioGroup>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* State */}
          <div className="space-y-2">
            <Label className="text-muted-foreground">State</Label>
            <Select value={formData.state} onValueChange={handleStateChange} required>
              <SelectTrigger className="input-field">
                <SelectValue placeholder="Select your state" />
              </SelectTrigger>
              <SelectContent className="bg-popover border-border">
                {states.map((state) => (
                  <SelectItem key={state} value={state} className="focus:bg-secondary">
                    {state}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* City */}
          <div className="space-y-2">
            <Label className="text-muted-foreground">City</Label>
            <Select 
              value={formData.city} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, city: value }))}
              disabled={!formData.state}
              required
            >
              <SelectTrigger className="input-field">
                <SelectValue placeholder={formData.state ? "Select your city" : "Select state first"} />
              </SelectTrigger>
              <SelectContent className="bg-popover border-border">
                {availableCities.map((city) => (
                  <SelectItem key={city} value={city} className="focus:bg-secondary">
                    {city}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </FormSection>

      {/* Financial Information */}
      <FormSection
        title="Financial Information"
        description="Your financial profile"
        icon={<Wallet className="h-5 w-5" />}
        step={2}
      >
        <div className="grid md:grid-cols-2 gap-6">
          {/* Employment Profile */}
          <div className="space-y-2">
            <Label className="text-muted-foreground">Employment Profile</Label>
            <Select 
              value={formData.employmentProfile} 
              onValueChange={(value) => setFormData(prev => ({ 
                ...prev, 
                employmentProfile: value,
                occupation: value === "Student" || value === "Unemployed" ? "" : prev.occupation
              }))}
              required
            >
              <SelectTrigger className="input-field">
                <SelectValue placeholder="Select employment type" />
              </SelectTrigger>
              <SelectContent className="bg-popover border-border">
                {employmentProfiles.map((profile) => (
                  <SelectItem key={profile} value={profile} className="focus:bg-secondary">
                    {profile}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Occupation */}
          <div className="space-y-2">
            <Label className="text-muted-foreground">Occupation</Label>
            <Select 
              value={formData.occupation} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, occupation: value }))}
              disabled={isOccupationDisabled}
            >
              <SelectTrigger className={`input-field ${isOccupationDisabled ? "opacity-50" : ""}`}>
                <SelectValue placeholder={isOccupationDisabled ? "Not applicable" : "Select your occupation"} />
              </SelectTrigger>
              <SelectContent className="bg-popover border-border">
                {occupations.map((occupation) => (
                  <SelectItem key={occupation} value={occupation} className="focus:bg-secondary">
                    {occupation}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Income */}
          <div className="space-y-2">
            <Label htmlFor="income" className="text-muted-foreground">Monthly Income</Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">₹</span>
              <Input
                id="income"
                type="number"
                min={0}
                placeholder="0"
                value={formData.income}
                onChange={(e) => setFormData(prev => ({ ...prev, income: e.target.value }))}
                className="input-field pl-8"
                required
              />
            </div>
          </div>

          {/* Existing Loans */}
          <Stepper
            value={formData.existingLoans}
            onChange={(value) => setFormData(prev => ({ ...prev, existingLoans: value }))}
            min={0}
            max={10}
            label="Existing Loans"
          />
        </div>

        {/* Credit History Length */}
        <SliderInput
          value={formData.creditHistoryLength}
          onChange={(value) => setFormData(prev => ({ ...prev, creditHistoryLength: value }))}
          min={6}
          max={360}
          label="Credit History Length"
          formatValue={formatMonths}
        />
      </FormSection>

      {/* Loan Request */}
      <FormSection
        title="Loan Request"
        description="Your loan requirements"
        icon={<CreditCard className="h-5 w-5" />}
        step={3}
      >
        {/* Loan Amount */}
        <SliderInput
          value={formData.loanAmount}
          onChange={(value) => setFormData(prev => ({ ...prev, loanAmount: value }))}
          min={10000}
          max={1500000}
          step={1000}
          label="Loan Amount"
          formatValue={formatCurrency}
        />

        {/* Loan Tenure */}
        <SliderInput
          value={formData.loanTenure}
          onChange={(value) => setFormData(prev => ({ ...prev, loanTenure: value }))}
          min={3}
          max={180}
          label="Loan Tenure"
          formatValue={formatMonths}
        />
      </FormSection>

      {/* Submit Button */}
      <div className="flex justify-center pt-4">
        <Button
          type="submit"
          size="lg"
          className="w-full md:w-auto px-12 py-6 text-lg font-semibold bg-primary hover:bg-primary/90 text-primary-foreground glow-effect animate-pulse-glow transition-all duration-300"
        >
          <Send className="mr-2 h-5 w-5" />
          Calculate My Score
        </Button>
      </div>
    </form>
  );
};

export default LoanForm;
