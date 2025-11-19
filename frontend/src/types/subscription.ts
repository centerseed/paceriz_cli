/**
 * 訂閱相關類型定義
 */

export type PaymentPlatform = 'stripe' | 'apple_iap' | 'google_play' | 'admin_grant' | 'unknown';

export interface Subscription {
  uid: string;
  trial_days: number;
  trial_start_at: string | null;
  trial_end_at: string | null;
  is_premium: boolean;
  premium_start_at: string | null;
  premium_end_at: string | null;
  total_extension_days: number;
  extension_history: ExtensionRecord[];
  payment_platform: PaymentPlatform | null;
  apple_original_transaction_id: string | null;
  apple_latest_receipt: string | null;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  google_play_order_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExtensionRecord {
  extended_at: string;
  days: number;
  reason: string;
  granted_by: string | null;
  note: string | null;
}

export interface SubscriptionDetail {
  subscription: {
    uid: string;
    status: string;
    is_premium: boolean;
    has_premium_access: boolean;
    can_start_trial: boolean;
    trial_days: number;
    trial_start_at: string | null;
    trial_end_at: string | null;
    total_extension_days: number;
    payment_platform: PaymentPlatform | null;
  };
  user: {
    uid: string;
    email: string | null;
    display_name: string | null;
    created_at: string | null;
  };
  invite_code: string | null;
}

export interface SubscriptionListResponse {
  data: Subscription[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}
