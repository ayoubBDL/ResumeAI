-- Add paypal_subscription_id column to subscriptions table
ALTER TABLE subscriptions
ADD COLUMN paypal_subscription_id TEXT;

-- Optional: Add a comment to explain the column
COMMENT ON COLUMN subscriptions.paypal_subscription_id IS 'PayPal Subscription ID for tracking external subscriptions';
