import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle, AlertCircle, X } from 'lucide-react';
import '../styles/animations.css';

export type ToastType = 'success' | 'error' | 'info';

interface ToastProps {
  message: string;
  type: ToastType;
  onClose: () => void;
  duration?: number;
}

export default function Toast({ message, type, onClose, duration = 2500 }: ToastProps) {
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsClosing(true);
      setTimeout(onClose, 200); // Wait for fade out animation
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(onClose, 200); // Wait for fade out animation
  };

  const bgColor = type === 'success' ? 'bg-green-50 border-green-200' :
                 type === 'error' ? 'bg-red-50 border-red-200' :
                 'bg-blue-50 border-blue-200';

  const textColor = type === 'success' ? 'text-green-800' :
                   type === 'error' ? 'text-red-800' :
                   'text-blue-800';

  const Icon = type === 'success' ? CheckCircle :
              type === 'error' ? XCircle :
              AlertCircle;

  return (
    <div 
      className={`fixed top-4 right-4 flex items-center p-4 mb-4 text-sm rounded-lg border ${bgColor} ${textColor} z-50 ${isClosing ? 'animate-fade-out' : 'animate-fade-in-down'}`}
      role="alert"
    >
      <Icon className="w-5 h-5 mr-2" />
      <span className="sr-only">{type}:</span>
      <div>{message}</div>
      <button
        type="button"
        className={`ml-4 -mx-1.5 -my-1.5 rounded-lg focus:ring-2 p-1.5 inline-flex h-8 w-8 ${textColor} hover:bg-opacity-25`}
        onClick={handleClose}
        aria-label="Close"
      >
        <span className="sr-only">Close</span>
        <X className="w-5 h-5" />
      </button>
    </div>
  );
}
