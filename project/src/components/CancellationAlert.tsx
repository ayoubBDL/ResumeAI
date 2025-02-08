import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

interface CancellationAlertProps {
  onConfirm: () => void;
  onClose: () => void;
  isLoading?: boolean;
}

export function CancellationAlert({ onConfirm, onClose, isLoading }: CancellationAlertProps) {
  return (
    <Alert variant="destructive" className="mt-4">
      <div className="flex items-start gap-4">
        <AlertCircle className="h-5 w-5" />
        <div className="flex-1">
          <AlertTitle>Cancel Subscription</AlertTitle>
          <AlertDescription className="mt-2">
            Are you sure you want to cancel your subscription? Your access will continue until the end of your current billing period.
          </AlertDescription>
          <div className="mt-4 flex gap-4">
            <Button
              variant="destructive"
              onClick={onConfirm}
              disabled={isLoading}
            >
              {isLoading ? 'Cancelling...' : 'Yes, Cancel'}
            </Button>
            <Button
              variant="outline"
              onClick={onClose}
            >
              Keep Subscription
            </Button>
          </div>
        </div>
      </div>
    </Alert>
  );
} 