import { PayPalButtons } from "@paypal/react-paypal-js";

const API_URL = import.meta.env.VITE_RESUME_API_URL || 'http://localhost:5050';

export default function PaypalButton({ 
    onApprove, 
    onCancel,
    plan_id
  }: { 
    onApprove: (data: any, actions: any) => Promise<void>, 
    onCancel: (data: any) => void,
    plan_id: string
  })  {

    const handleSubscription = async (data: any, actions: any) => {
        console.log("Create subscription data", plan_id);
        return actions.subscription.create({
            plan_id: plan_id,
            application_context: {
                shipping_preference: "NO_SHIPPING",
                return_url: `${import.meta.env.VITE_PAYPAL_RETURN_URL}`,
                cancel_url: `${import.meta.env.VITE_PAYPAL_CANCEL_URL}`
            }
        });
    }

    const handleApprove = (data: any, actions: any) => {
        console.log("Subscription approved", data);
        console.log("Subscription Actions ", actions);
        if(data.subscriptionID){
            onApprove(data, actions);
            return actions.redirect();
        }
    }

    const handleCancel = (data: any) => {
        console.log("Subscription cancelled", data);
        onCancel(data);
    }
    return (
        <div>
            <PayPalButtons
                createSubscription={handleSubscription}
                style={{shape: "rect", label: "subscribe"}}
                onApprove={handleApprove}
                onCancel={handleCancel}
            />
        </div>
    );
}