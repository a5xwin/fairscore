import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { useAuth } from '@/context/AuthContext';
import { useState } from 'react';
import { toast } from 'sonner';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useEffect } from 'react';
import { authService } from '@/services/authService';
import { states, statesWithCities, occupations, employmentProfiles } from '@/data/locationData';
import { Skeleton } from '@/components/ui/skeleton';
import { Pencil, Save, X, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

type SavedPersonal = {
    dob: string;
    gender: string;
    state: string;
    city: string;
    phone: string;
};

type SavedEmployment = {
    empProfile: string;
    occupation: string;
    customOccupation: string;
    income: string;
};

type SavedCredit = {
    creditHistoryYr: string;
    creditHistoryMon: string;
    loanNo: string;
    assetValue: string;
};

const Profile = () => {
    const { user } = useAuth();
    
    // Loading and error states
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [savingSection, setSavingSection] = useState<string | null>(null);

    const [savedPersonal, setSavedPersonal] = useState<SavedPersonal>({
        dob: '',
        gender: '',
        state: '',
        city: '',
        phone: '',
    });
    const [savedEmployment, setSavedEmployment] = useState<SavedEmployment>({
        empProfile: '',
        occupation: '',
        customOccupation: '',
        income: '',
    });
    const [savedCredit, setSavedCredit] = useState<SavedCredit>({
        creditHistoryYr: '',
        creditHistoryMon: '',
        loanNo: '',
        assetValue: '',
    });
    
    // Personal info
    const [personalEditing, setPersonalEditing] = useState(false);
    const [dob, setDob] = useState('');
    const [gender, setGender] = useState('');
    const [state, setState] = useState('');
    const [city, setCity] = useState('');
    const [phone, setPhone] = useState('');
    
    // Employment info
    const [employmentEditing, setEmploymentEditing] = useState(false);
    const [empProfile, setEmpProfile] = useState('');
    const [occupation, setOccupation] = useState('');
    const [customOccupation, setCustomOccupation] = useState('');
    const [income, setIncome] = useState('');
    
    // Credit info
    const [creditEditing, setCreditEditing] = useState(false);
    const [creditHistoryYr, setCreditHistoryYr] = useState('');
    const [creditHistoryMon, setCreditHistoryMon] = useState('');
    const [loanNo, setLoanNo] = useState('');
    const [assetValue, setAssetValue] = useState('');
    
    // Loan info (read-only)
    const [loanAmount, setLoanAmount] = useState<number | null>(null);
    const [loanTenureYr, setLoanTenureYr] = useState<number | null>(null);
    const [loanTenureMon, setLoanTenureMon] = useState<number | null>(null);
    const [loanPurpose, setLoanPurpose] = useState('');

    const cities = state ? statesWithCities[state] || [] : [];
    const isOccupationDisabled = empProfile === 'Student' || empProfile === 'Unemployed';
    const displayOccupation = occupation === 'Other' ? customOccupation : occupation;

    // Fetch all borrower data on mount
    useEffect(() => {
        const fetchBorrowerData = async () => {
            if (!user?.id) return;
            try {
                setLoading(true);
                setError('');

                const [loanData, profileData] = await Promise.all([
                    authService.getLoanInfo(user.id),
                    authService.getBorrowerProfile(user.id),
                ]);

                setLoanAmount(loanData.loanAmount);
                setLoanTenureYr(loanData.loanTenureYr);
                setLoanTenureMon(loanData.loanTenureMon);
                setLoanPurpose(loanData.purpose);

                setDob(profileData.dob || '');
                setGender(profileData.gender || '');
                setState(profileData.state || '');
                setCity(profileData.city || '');
                setPhone(profileData.phone || '');

                setEmpProfile(profileData.empProfile || '');
                let loadedOccupation = '';
                let loadedCustomOccupation = '';
                if (profileData.occupation && occupations.includes(profileData.occupation)) {
                    loadedOccupation = profileData.occupation;
                } else {
                    loadedOccupation = profileData.occupation ? 'Other' : '';
                    loadedCustomOccupation = profileData.occupation || '';
                }
                setOccupation(loadedOccupation);
                setCustomOccupation(loadedCustomOccupation);
                setIncome(profileData.income ? String(profileData.income) : '');

                setCreditHistoryYr(String(profileData.creditHistoryYr ?? ''));
                setCreditHistoryMon(String(profileData.creditHistoryMon ?? ''));
                setLoanNo(profileData.loanNo ? String(profileData.loanNo) : '');
                setAssetValue(profileData.assetValue ? String(profileData.assetValue) : '');

                setSavedPersonal({
                    dob: profileData.dob || '',
                    gender: profileData.gender || '',
                    state: profileData.state || '',
                    city: profileData.city || '',
                    phone: profileData.phone || '',
                });
                setSavedEmployment({
                    empProfile: profileData.empProfile || '',
                    occupation: loadedOccupation,
                    customOccupation: loadedCustomOccupation,
                    income: profileData.income ? String(profileData.income) : '',
                });
                setSavedCredit({
                    creditHistoryYr: String(profileData.creditHistoryYr ?? ''),
                    creditHistoryMon: String(profileData.creditHistoryMon ?? ''),
                    loanNo: profileData.loanNo ? String(profileData.loanNo) : '',
                    assetValue: profileData.assetValue ? String(profileData.assetValue) : '',
                });
                
            } catch (err) {
                setError('Failed to load profile data. Please try again.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        
        fetchBorrowerData();
    }, [user?.id]);

    // Personal info save handler
    const handleSavePersonal = async () => {
        if (!user?.id || !dob || !gender || !state || !city || !phone) {
            toast.error('Please fill all personal information fields.');
            return;
        }
        
        if (!/^\d{10}$/.test(phone)) {
            toast.error('Phone number must be 10 digits.');
            return;
        }

        setSavingSection('personal');
        try {
            await authService.updatePersonalInfo({
                userid: user.id,
                dob,
                gender,
                state,
                city,
                phone,
            });
            setSavedPersonal({ dob, gender, state, city, phone });
            setPersonalEditing(false);
            toast.success('Personal information updated successfully!');
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string } } };
            toast.error(e?.response?.data?.detail || 'Failed to update personal information.');
        } finally {
            setSavingSection(null);
        }
    };

    // Employment info save handler
    const handleSaveEmployment = async () => {
        if (!empProfile || !occupation || !income) {
            toast.error('Please fill all employment information fields.');
            return;
        }
        
        if (occupation === 'Other' && !customOccupation.trim()) {
            toast.error('Please specify your occupation.');
            return;
        }

        setSavingSection('employment');
        try {
            await authService.updateEmploymentInfo({
                userid: user.id!,
                empProfile,
                occupation: occupation === 'Other' ? customOccupation : occupation,
                income: Number(income),
            });
            setSavedEmployment({ empProfile, occupation, customOccupation, income });
            setEmploymentEditing(false);
            toast.success('Employment information updated successfully!');
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string } } };
            toast.error(e?.response?.data?.detail || 'Failed to update employment information.');
        } finally {
            setSavingSection(null);
        }
    };

    // Credit info save handler
    const handleSaveCredit = async () => {
        if (creditHistoryYr === '' || creditHistoryMon === '' || loanNo === '' || assetValue === '') {
            toast.error('Please fill all credit information fields.');
            return;
        }

        setSavingSection('credit');
        try {
            await authService.updateCreditInfo({
                userid: user.id!,
                creditHistoryYr: Number(creditHistoryYr),
                creditHistoryMon: Number(creditHistoryMon),
                loanNo: Number(loanNo),
                assetValue: Number(assetValue),
            });
            setSavedCredit({ creditHistoryYr, creditHistoryMon, loanNo, assetValue });
            setCreditEditing(false);
            toast.success('Credit information updated successfully!');
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string } } };
            toast.error(e?.response?.data?.detail || 'Failed to update credit information.');
        } finally {
            setSavingSection(null);
        }
    };

    // Cancel handlers
    const handleCancelPersonal = () => {
        setDob(savedPersonal.dob);
        setGender(savedPersonal.gender);
        setState(savedPersonal.state);
        setCity(savedPersonal.city);
        setPhone(savedPersonal.phone);
        setPersonalEditing(false);
    };

    const handleCancelEmployment = () => {
        setEmpProfile(savedEmployment.empProfile);
        setOccupation(savedEmployment.occupation);
        setCustomOccupation(savedEmployment.customOccupation);
        setIncome(savedEmployment.income);
        setEmploymentEditing(false);
    };

    const handleCancelCredit = () => {
        setCreditHistoryYr(savedCredit.creditHistoryYr);
        setCreditHistoryMon(savedCredit.creditHistoryMon);
        setLoanNo(savedCredit.loanNo);
        setAssetValue(savedCredit.assetValue);
        setCreditEditing(false);
    };

    return (
        <div className="flex-1 space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Profile Settings</h2>
            </div>

            {error && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {/* Personal Information */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-3">
                    <div>
                        <CardTitle>Personal Information</CardTitle>
                        <CardDescription>Update your personal details.</CardDescription>
                    </div>
                    {!loading && !personalEditing && (
                        <Button variant="outline" size="sm" onClick={() => setPersonalEditing(true)}>
                            <Pencil className="h-4 w-4 mr-1" /> Edit
                        </Button>
                    )}
                </CardHeader>

                <CardContent className="space-y-4">
                    {loading ? (
                        <div className="space-y-4">
                            {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
                        </div>
                    ) : personalEditing ? (
                        <>
                            <div className="space-y-2">
                                <Label htmlFor="dob">Date of Birth</Label>
                                <Input
                                    id="dob"
                                    type="date"
                                    value={dob}
                                    onChange={(e) => setDob(e.target.value)}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label>Gender</Label>
                                <Select value={gender} onValueChange={setGender}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select gender" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {['Male', 'Female', 'Other'].map((g) => (
                                            <SelectItem key={g} value={g}>{g}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>State</Label>
                                    <Select value={state} onValueChange={(v) => { setState(v); setCity(''); }}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select state" />
                                        </SelectTrigger>
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
                                        <SelectTrigger>
                                            <SelectValue placeholder={state ? 'Select city' : 'Select state first'} />
                                        </SelectTrigger>
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
                                    value={phone}
                                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                                />
                            </div>
                        </>
                    ) : (
                        <div className="grid gap-4 sm:grid-cols-2">
                            <div>
                                <p className="text-sm text-muted-foreground">Date of Birth</p>
                                <p className="text-lg font-semibold">{dob || '—'}</p>
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground">Gender</p>
                                <p className="text-lg font-semibold">{gender || '—'}</p>
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground">State</p>
                                <p className="text-lg font-semibold">{state || '—'}</p>
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground">City</p>
                                <p className="text-lg font-semibold">{city || '—'}</p>
                            </div>
                            <div className="sm:col-span-2">
                                <p className="text-sm text-muted-foreground">Phone Number</p>
                                <p className="text-lg font-semibold">{phone || '—'}</p>
                            </div>
                        </div>
                    )}
                </CardContent>

                {personalEditing && (
                    <CardFooter className="flex justify-end gap-2">
                        <Button 
                            variant="outline" 
                            onClick={handleCancelPersonal}
                            disabled={savingSection === 'personal'}
                        >
                            <X className="h-4 w-4 mr-1" /> Cancel
                        </Button>
                        <Button 
                            onClick={handleSavePersonal}
                            disabled={savingSection === 'personal'}
                        >
                            <Save className="h-4 w-4 mr-1" /> {savingSection === 'personal' ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </CardFooter>
                )}
            </Card>

            <Separator />

            {/* Employment Information */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-3">
                    <div>
                        <CardTitle>Employment Information</CardTitle>
                        <CardDescription>Update your employment details.</CardDescription>
                    </div>
                    {!loading && !employmentEditing && (
                        <Button variant="outline" size="sm" onClick={() => setEmploymentEditing(true)}>
                            <Pencil className="h-4 w-4 mr-1" /> Edit
                        </Button>
                    )}
                </CardHeader>

                <CardContent className="space-y-4">
                    {loading ? (
                        <div className="space-y-4">
                            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
                        </div>
                    ) : employmentEditing ? (
                        <>
                            <div className="space-y-2">
                                <Label>Employment Profile</Label>
                                <Select value={empProfile} onValueChange={setEmpProfile}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select employment type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {employmentProfiles.map((ep) => (
                                            <SelectItem key={ep} value={ep}>{ep}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <Label>Occupation</Label>
                                <Select value={occupation} onValueChange={setOccupation} disabled={isOccupationDisabled}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select occupation" />
                                    </SelectTrigger>
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
                                    value={income}
                                    onChange={(e) => setIncome(e.target.value)}
                                />
                            </div>
                        </>
                    ) : (
                        <div className="grid gap-4 sm:grid-cols-2">
                            <div>
                                <p className="text-sm text-muted-foreground">Employment Profile</p>
                                <p className="text-lg font-semibold">{empProfile || '—'}</p>
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground">Occupation</p>
                                <p className="text-lg font-semibold">{displayOccupation || '—'}</p>
                            </div>
                            <div className="sm:col-span-2">
                                <p className="text-sm text-muted-foreground">Monthly Income</p>
                                <p className="text-lg font-semibold">₹{income ? Number(income).toLocaleString('en-IN') : '—'}</p>
                            </div>
                        </div>
                    )}
                </CardContent>

                {employmentEditing && (
                    <CardFooter className="flex justify-end gap-2">
                        <Button 
                            variant="outline" 
                            onClick={handleCancelEmployment}
                            disabled={savingSection === 'employment'}
                        >
                            <X className="h-4 w-4 mr-1" /> Cancel
                        </Button>
                        <Button 
                            onClick={handleSaveEmployment}
                            disabled={savingSection === 'employment'}
                        >
                            <Save className="h-4 w-4 mr-1" /> {savingSection === 'employment' ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </CardFooter>
                )}
            </Card>

            <Separator />

            {/* Credit History Information */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-3">
                    <div>
                        <CardTitle>Credit History</CardTitle>
                        <CardDescription>Update your credit profile details.</CardDescription>
                    </div>
                    {!loading && !creditEditing && (
                        <Button variant="outline" size="sm" onClick={() => setCreditEditing(true)}>
                            <Pencil className="h-4 w-4 mr-1" /> Edit
                        </Button>
                    )}
                </CardHeader>

                <CardContent className="space-y-4">
                    {loading ? (
                        <div className="space-y-4">
                            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
                        </div>
                    ) : creditEditing ? (
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
                    ) : (
                        <div className="grid gap-4 sm:grid-cols-2">
                            <div>
                                <p className="text-sm text-muted-foreground">Credit History Length</p>
                                <p className="text-lg font-semibold">
                                    {creditHistoryYr || creditHistoryMon ? `${creditHistoryYr || 0} yrs ${creditHistoryMon || 0} mos` : '—'}
                                </p>
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground">Existing Loans</p>
                                <p className="text-lg font-semibold">{loanNo || '—'}</p>
                            </div>
                            <div className="sm:col-span-2">
                                <p className="text-sm text-muted-foreground">Asset Value</p>
                                <p className="text-lg font-semibold">₹{assetValue ? Number(assetValue).toLocaleString('en-IN') : '—'}</p>
                            </div>
                        </div>
                    )}
                </CardContent>

                {creditEditing && (
                    <CardFooter className="flex justify-end gap-2">
                        <Button 
                            variant="outline" 
                            onClick={handleCancelCredit}
                            disabled={savingSection === 'credit'}
                        >
                            <X className="h-4 w-4 mr-1" /> Cancel
                        </Button>
                        <Button 
                            onClick={handleSaveCredit}
                            disabled={savingSection === 'credit'}
                        >
                            <Save className="h-4 w-4 mr-1" /> {savingSection === 'credit' ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </CardFooter>
                )}
            </Card>

            <Separator />

            {/* Loan Details (Read-Only) */}
            <Card>
                <CardHeader>
                    <CardTitle>Current Loan Details</CardTitle>
                    <CardDescription>View and edit your loan details on the Loan Details page.</CardDescription>
                </CardHeader>

                <CardContent>
                    {loading ? (
                        <div className="space-y-4">
                            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
                        </div>
                    ) : (
                        <div className="grid gap-4 sm:grid-cols-2">
                            <div>
                                <p className="text-sm text-muted-foreground">Loan Amount</p>
                                <p className="text-lg font-semibold">₹{loanAmount ? loanAmount.toLocaleString('en-IN') : '—'}</p>
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground">Loan Tenure</p>
                                <p className="text-lg font-semibold">
                                    {loanTenureYr || loanTenureMon ? `${loanTenureYr || 0} yrs ${loanTenureMon || 0} mos` : '—'}
                                </p>
                            </div>
                            <div className="sm:col-span-2">
                                <p className="text-sm text-muted-foreground">Purpose</p>
                                <p className="text-lg font-semibold">{loanPurpose || '—'}</p>
                            </div>
                        </div>
                    )}
                </CardContent>

                <CardFooter>
                    <Button variant="outline">Edit Loan Details</Button>
                </CardFooter>
            </Card>
        </div>
    );
};

export default Profile;
