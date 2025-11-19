/**
 * 邀請碼相關類型定義
 */

export interface InviteCode {
  code: string;
  owner_uid: string;
  usage_count: number;
  max_usage: number;
  reward_days: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InviteCodeDetail {
  invite_code: InviteCode;
  owner: {
    uid: string;
    has_subscription: boolean;
    is_premium: boolean;
  };
  statistics: {
    total_usages: number;
    rewarded_usages: number;
    pending_rewards: number;
  };
}

export interface InviteCodeUsage {
  invitee_uid: string;
  inviter_uid: string;
  used_at: string;
  reward_granted: boolean;
  reward_granted_at: string | null;
  reward_days: number;
  inviter_past_refund_period: boolean;
  invitee_past_refund_period: boolean;
}

export interface InviteCodeStats {
  total_codes: number;
  active_codes: number;
  inactive_codes: number;
  total_usages: number;
  rewarded_usages: number;
  pending_rewards: number;
  conversion_rate: number;
}

export interface InviteCodeListResponse {
  data: InviteCode[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}
