import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Upload, FileText, CheckCircle, X } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

const Documents = () => {
    const [idProof, setIdProof] = useState<File | null>(null);
    const [bankStatement, setBankStatement] = useState<File | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, setFile: (f: File | null) => void) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!idProof || !bankStatement) {
            toast.error('Please select both files.');
            return;
        }

        setIsLoading(true);
        // Simulate upload
        await new Promise(resolve => setTimeout(resolve, 2000));

        toast.success('Documents uploaded successfully!');
        setIsLoading(false);
        // Reset or redirect
    };

    const FilePreview = ({ file, onRemove }: { file: File, onRemove: () => void }) => (
        <div className="flex items-center justify-between p-3 border rounded-lg bg-muted/50">
            <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-primary" />
                <div className="flex flex-col">
                    <span className="text-sm font-medium truncate max-w-[200px]">{file.name}</span>
                    <span className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                </div>
            </div>
            <Button variant="ghost" size="icon" onClick={onRemove}>
                <X className="h-4 w-4" />
            </Button>
        </div>
    );

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <h2 className="text-3xl font-bold tracking-tight">Upload Documents</h2>
            <Card>
                <CardHeader>
                    <CardTitle>Required Documents</CardTitle>
                    <CardDescription>
                        Please upload valid identification and financial documents to process your loan.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="space-y-4">
                        <Label>Government ID Proof</Label>
                        {!idProof ? (
                            <div className="border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-accent/50 transition-colors relative">
                                <Upload className="h-8 w-8 text-muted-foreground mb-2" />
                                <span className="text-sm text-muted-foreground">Click to upload ID (PDF, JPG)</span>
                                <Input
                                    type="file"
                                    className="absolute inset-0 opacity-0 cursor-pointer"
                                    accept=".pdf,.jpg,.jpeg,.png"
                                    onChange={(e) => handleFileChange(e, setIdProof)}
                                />
                            </div>
                        ) : (
                            <FilePreview file={idProof} onRemove={() => setIdProof(null)} />
                        )}
                    </div>

                    <div className="space-y-4">
                        <Label>Bank Statements (Last 6 Months)</Label>
                        {!bankStatement ? (
                            <div className="border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-accent/50 transition-colors relative">
                                <Upload className="h-8 w-8 text-muted-foreground mb-2" />
                                <span className="text-sm text-muted-foreground">Click to upload Statements (PDF)</span>
                                <Input
                                    type="file"
                                    className="absolute inset-0 opacity-0 cursor-pointer"
                                    accept=".pdf"
                                    onChange={(e) => handleFileChange(e, setBankStatement)}
                                />
                            </div>
                        ) : (
                            <FilePreview file={bankStatement} onRemove={() => setBankStatement(null)} />
                        )}
                    </div>
                </CardContent>
                <CardFooter>
                    <Button onClick={handleUpload} className="w-full" disabled={isLoading || !idProof || !bankStatement}>
                        {isLoading ? 'Uploading...' : 'Upload & Verify'}
                    </Button>
                </CardFooter>
            </Card>
        </div>
    );
};

export default Documents;
