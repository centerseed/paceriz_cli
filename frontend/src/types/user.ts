/**
 * 用戶相關的 TypeScript 類型定義
 */

export interface User {
  uid: string;
  email?: string;
  display_name?: string;
  preferred_language?: string;
  vdot?: number;
  is_admin?: boolean;
  data_source?: 'garmin' | 'strava' | 'apple_health';  // 主要數據來源
  garmin_connected?: boolean;
  strava_connected?: boolean;
  apple_health_connected?: boolean;
  created_at?: any;  // Firestore Timestamp
  updated_at?: any;  // Firestore Timestamp
  last_login_at?: any;  // Firestore Timestamp
}

export interface UserListResponse {
  data: User[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}
