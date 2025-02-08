import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

interface AlertProps {
  error: string;
  message: string;
  action: 'purchase' | 'confirm' | 'retry' | 'close';
  onAction?: () => void;
  onClose: () => void;
  actionLabel?: string;
  disabled?: boolean;
}

export function AlertDialog({ 
  error, 
  message, 
  action, 
  onAction, 
  onClose, 
  actionLabel,
  disabled 
}: AlertProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <AlertTitle className="text-lg font-semibold">{error}</AlertTitle>
          </div>
          <AlertDescription className="text-gray-600">
            {message}
          </AlertDescription>
          <div className="flex justify-end gap-3 mt-4">
            <Button
              variant="outline"
              onClick={onClose}
            >
              {action === 'confirm' ? 'Keep Subscription' : 'Close'}
            </Button>
            {action !== 'close' && (
              <Button
                variant={action === 'confirm' ? 'destructive' : 'default'}
                onClick={onAction}
                disabled={disabled}
              >
                {actionLabel || (
                  action === 'purchase' ? 'Purchase Credits' :
                  action === 'confirm' ? 'Yes, Cancel' :
                  'Retry'
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
