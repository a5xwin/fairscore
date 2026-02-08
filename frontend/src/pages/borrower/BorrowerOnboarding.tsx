import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { statesWithCities, states, occupations, employmentProfiles, loanPurposes } from '@/data/locationData';
import { authService } from '@/services/authService';
import { User, CalendarDays, MapPin, Phone, Briefcase, IndianRupee, History, Landmark, ChevronRight, ChevronLeft, Check } from 'lucide-react';

const steps = [
  { title: 'Personal Information', icon: User },
  { title: 'Employment Details', icon: Briefcase },
  { title: 'Credit History', icon: History },
  { title: 'Loan Details', icon: Landmark },
];

const BorrowerOnboarding = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Personal Information
  const [dob, setDob] = useState('');
  const [gender, setGender] = useState('');
  const [state, setState] = useState('');
  const [city, setCity] = useState('');
  const [phone, setPhone] = useState('');

  // Employment Details
  const [empProfile, setEmpProfile] = useState('');
  const [occupation, setOccupation] = useState('');
  const [customOccupation, setCustomOccupation] = useState('');
  const [income, setIncome] = useState('');

  // Credit History
  const [creditHistoryYr, setCreditHistoryYr] = useState('');
  const [creditHistoryMon, setCreditHistoryMon] = useState('');
  const [loanNo, setLoanNo] = useState('');
  const [assetValue, setAssetValue] = useState('');

  // Loan Details
  const [loanAmount, setLoanAmount] = useState('');
  const [loanTenureYr, setLoanTenureYr] = useState('');
  const [loanTenureMon, setLoanTenureMon] = useState('');
  const [purpose, setPurpose] = useState('');

  const cities = state ? statesWithCities[state] || [] : [];

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 0:
        if (!dob || !gender || !state || !city || !phone) {
          toast.error('Please fill all personal information fields.');
          return false;
        }
        if (!/^\d{10}$/.test(phone)) {
          toast.error('Phone number must be 10 digits.');
          return false;
        }
        return true;
      case 1:
        if (!empProfile || !occupation || !income) {
          toast.error('Please fill all employment details.');
          return false;
        }
        if (occupation === 'Other' && !customOccupation.trim()) {
          toast.error('Please enter your specific occupation.');
          return false;
        }
        return true;
      case 2:
        if (creditHistoryYr === '' || creditHistoryMon === '' || loanNo === '' || assetValue === '') {
          toast.error('Please fill all credit history fields.');
          return false;
        }
        return true;
      case 3:
        if (!loanAmount || loanTenureYr === '' || loanTenureMon === '' || !purpose) {
          toast.error('Please fill all loan details.');
          return false;
        }
        return true;
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep((prev) => Math.min(prev + 1, steps.length - 1));
    }
  };

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;
    setIsSubmitting(true);

    try {
      const payload = {
        userid: user?.id ?? '',
        dob,
        gender,
        state,
        city,
        phone,
        empProfile,
        occupation: occupation === 'Other' ? customOccupation : occupation,
        income: Number(income),
        creditHistoryYr: Number(creditHistoryYr),
        creditHistoryMon: Number(creditHistoryMon),
        loanNo: Number(loanNo),
        assetValue: Number(assetValue),
        loanAmount: Number(loanAmount),
        loanTenureYr: Number(loanTenureYr),
        loanTenureMon: Number(loanTenureMon),
        purpose,
      };

      await authService.submitBorrowerDetails(payload);
      localStorage.setItem('onboarded', 'true');
      toast.success('Details submitted successfully!');
      navigate('/borrower/dashboard');
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      const msg = err?.response?.data?.detail || 'Failed to submit details. Please try again.';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-muted/40 py-8 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold">Welcome, {user?.name}!</h1>
          <p className="text-muted-foreground">Let's set up your profile to get you the best loan offers.</p>
        </div>

        {/* Step Indicator */}
        <div className="flex items-center justify-center gap-2">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = index === currentStep;
            const isCompleted = index < currentStep;
            return (
              <div key={index} className="flex items-center">
                <div className={`flex items-center gap-2 px-3 py-2 rounded-full text-sm font-medium transition-all ${
                  isActive ? 'bg-primary text-primary-foreground' :
                  isCompleted ? 'bg-primary/20 text-primary' :
                  'bg-muted text-muted-foreground'
                }`}>
                  {isCompleted ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                  <span className="hidden sm:inline">{step.title}</span>
                  <span className="sm:hidden">{index + 1}</span>
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-6 h-0.5 mx-1 ${index < currentStep ? 'bg-primary' : 'bg-muted-foreground/30'}`} />
                )}
              </div>
            );
          })}
        </div>

        {/* Form Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {(() => { const Icon = steps[currentStep].icon; return <Icon className="h-5 w-5" />; })()}
              {steps[currentStep].title}
            </CardTitle>
            <CardDescription>
              Step {currentStep + 1} of {steps.length}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Step 1: Personal Information */}
            {currentStep === 0 && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="dob">Date of Birth</Label>
                  <Input
                    id="dob"
                    type="date"
                    required
                    value={dob}
                    onChange={(e) => setDob(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Gender</Label>
                  <RadioGroup value={gender} onValueChange={setGender} className="flex gap-4">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="Male" id="male" />
                      <Label htmlFor="male">Male</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="Female" id="female" />
                      <Label htmlFor="female">Female</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="Other" id="other" />
                      <Label htmlFor="other">Other</Label>
                    </div>
                  </RadioGroup>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>State / UT</Label>
                    <Select value={state} onValueChange={(v) => { setState(v); setCity(''); }}>
                      <SelectTrigger><SelectValue placeholder="Select state" /></SelectTrigger>
                      <SelectContent>
                        {states.map((s) => (
                          <SelectItem key={s} value={s}>{s}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>City</Label>
                    <Select value={city} onValueChange={setCity} disabled={!state}>
                      <SelectTrigger><SelectValue placeholder={state ? "Select city" : "Select state first"} /></SelectTrigger>
                      <SelectContent>
                        {cities.map((c) => (
                          <SelectItem key={c} value={c}>{c}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="10-digit phone number"
                    maxLength={10}
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                  />
                </div>
              </>
            )}

            {/* Step 2: Employment Details */}
            {currentStep === 1 && (
              <>
                <div className="space-y-2">
                  <Label>Employment Profile</Label>
                  <Select value={empProfile} onValueChange={setEmpProfile}>
                    <SelectTrigger><SelectValue placeholder="Select employment type" /></SelectTrigger>
                    <SelectContent>
                      {employmentProfiles.map((ep) => (
                        <SelectItem key={ep} value={ep}>{ep}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Occupation</Label>
                  <Select value={occupation} onValueChange={setOccupation}>
                    <SelectTrigger><SelectValue placeholder="Select occupation" /></SelectTrigger>
                    <SelectContent>
                      {occupations.map((o) => (
                        <SelectItem key={o} value={o}>{o}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {occupation === 'Other' && (
                  <div className="space-y-2">
                    <Label htmlFor="customOccupation">Specify Occupation</Label>
                    <Input
                      id="customOccupation"
                      placeholder="Enter your occupation"
                      required
                      value={customOccupation}
                      onChange={(e) => setCustomOccupation(e.target.value)}
                    />
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="income">Monthly Income (₹)</Label>
                  <Input
                    id="income"
                    type="number"
                    placeholder="e.g. 50000"
                    min={0}
                    required
                    value={income}
                    onChange={(e) => setIncome(e.target.value)}
                  />
                </div>
              </>
            )}

            {/* Step 3: Credit History */}
            {currentStep === 2 && (
              <>
                <div className="space-y-2">
                  <Label>Length of Credit History</Label>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <Label htmlFor="creditYr" className="text-xs text-muted-foreground">Years</Label>
                      <Input
                        id="creditYr"
                        type="number"
                        placeholder="Years"
                        min={0}
                        max={50}
                        value={creditHistoryYr}
                        onChange={(e) => setCreditHistoryYr(e.target.value)}
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="creditMon" className="text-xs text-muted-foreground">Months</Label>
                      <Input
                        id="creditMon"
                        type="number"
                        placeholder="Months"
                        min={0}
                        max={11}
                        value={creditHistoryMon}
                        onChange={(e) => setCreditHistoryMon(e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="loanNo">Number of Existing Loans</Label>
                  <Input
                    id="loanNo"
                    type="number"
                    placeholder="e.g. 2"
                    min={0}
                    value={loanNo}
                    onChange={(e) => setLoanNo(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="assetValue">Approximate Value of Assets (₹)</Label>
                  <Input
                    id="assetValue"
                    type="number"
                    placeholder="e.g. 500000"
                    min={0}
                    value={assetValue}
                    onChange={(e) => setAssetValue(e.target.value)}
                  />
                </div>
              </>
            )}

            {/* Step 4: Loan Details */}
            {currentStep === 3 && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="loanAmount">Requesting Loan Amount (₹)</Label>
                  <Input
                    id="loanAmount"
                    type="number"
                    placeholder="e.g. 200000"
                    min={0}
                    required
                    value={loanAmount}
                    onChange={(e) => setLoanAmount(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Expected Loan Tenure</Label>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <Label htmlFor="tenureYr" className="text-xs text-muted-foreground">Years</Label>
                      <Input
                        id="tenureYr"
                        type="number"
                        placeholder="Years"
                        min={0}
                        max={30}
                        value={loanTenureYr}
                        onChange={(e) => setLoanTenureYr(e.target.value)}
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="tenureMon" className="text-xs text-muted-foreground">Months</Label>
                      <Input
                        id="tenureMon"
                        type="number"
                        placeholder="Months"
                        min={0}
                        max={11}
                        value={loanTenureMon}
                        onChange={(e) => setLoanTenureMon(e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Purpose of Loan</Label>
                  <Select value={purpose} onValueChange={setPurpose}>
                    <SelectTrigger><SelectValue placeholder="Select purpose" /></SelectTrigger>
                    <SelectContent>
                      {loanPurposes.map((p) => (
                        <SelectItem key={p} value={p}>{p}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}
          </CardContent>

          <CardFooter className="flex justify-between">
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={currentStep === 0}
            >
              <ChevronLeft className="h-4 w-4 mr-1" /> Back
            </Button>

            {currentStep < steps.length - 1 ? (
              <Button onClick={handleNext}>
                Next <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            ) : (
              <Button onClick={handleSubmit} disabled={isSubmitting}>
                {isSubmitting ? 'Submitting...' : 'Submit Details'}
              </Button>
            )}
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export default BorrowerOnboarding;
