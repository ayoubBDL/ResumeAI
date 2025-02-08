-- Add cancelled_at column to subscriptions table
ALTER TABLE subscriptions
ADD COLUMN cancelled_at TIMESTAMP WITH TIME ZONE;

-- Optional: Add a comment to explain the column
COMMENT ON COLUMN subscriptions.cancelled_at IS 'Timestamp when the subscription was cancelled';

-- Optional: Add an index for better query performance on cancelled subscriptions
CREATE INDEX idx_subscriptions_cancelled_at ON subscriptions(cancelled_at); 