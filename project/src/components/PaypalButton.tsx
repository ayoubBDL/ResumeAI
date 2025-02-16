import { PayPalButtons } from "@paypal/react-paypal-js";

export default function PaypalButton({ 
    onApprove, 
    onCancel,
    plan_id,
    isSubscription = true,
    amount,
    description,
    onCreditsUpdate
  }: { 
    onApprove: (data: any, actions: any) => Promise<void>, 
    onCancel: (data: any) => void,
    plan_id?: string,
    isSubscription?: boolean,
    amount?: string,
    description?: string,
    onCreditsUpdate?: () => Promise<void>
  })  {

    const createSubscription = async (data: any, actions: any) => {
        if (!plan_id) {
            console.error("No plan_id provided for subscription");
            return;
        }
        return actions.subscription.create({
            plan_id: plan_id,
            application_context: {
                shipping_preference: "NO_SHIPPING"
            }
        });
    }

    const createOrder = async (data: any, actions: any) => {
        if (!amount) {
          throw new Error('Amount is required for one-time payment');
        }

        return await actions.order.create({
          purchase_units: [{
            amount: {
              value: amount,
              currency_code: "USD"
            },
            description: description || 'One-time payment'
          }]
        });
    };

    const onApproveHandler = async (data: any, actions: any) => {
        try {
          if (isSubscription) {
            // For subscriptions, just pass the data to parent
            await onApprove(data, actions);
          } else {
            // For one-time payments, capture the order first
            const orderData = await actions.order.capture();
            await onApprove({
              orderID: data.orderID,
              ...orderData
            }, actions);
          }
          
          // Update credits after successful payment
          if (onCreditsUpdate) {
            await onCreditsUpdate();
          }
        } catch (error) {
          console.error('PayPal approval error:', error);
          throw error;
        }
    };

    const handleCancel = (data: any) => {
        onCancel(data);
    }

    const style = {
        shape: "rect",
        label: isSubscription ? "subscribe" : "pay"
    } as any;

    return (
        <div>
            {isSubscription ? (
                <PayPalButtons
                  createSubscription={createSubscription}
                  onApprove={onApproveHandler}
                  onCancel={handleCancel}
                  style={style}
                />
              ) : (
                <PayPalButtons
                  createOrder={createOrder}
                  onApprove={onApproveHandler}
                  onCancel={handleCancel}
                  style={style}
                />
              )}
        </div>
    );
}