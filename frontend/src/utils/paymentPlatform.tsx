/**
 * 付款平台相關工具函數
 */
import React from 'react';
import { CreditCard, Apple, Smartphone, Gift, HelpCircle } from 'lucide-react';
import { PaymentPlatform } from '../types/subscription';

/**
 * 獲取付款平台的顯示信息
 */
export function getPaymentPlatformInfo(platform: PaymentPlatform | null | undefined): {
  icon: React.ReactNode;
  label: string;
  color: string;
  bgColor: string;
} {
  switch (platform) {
    case 'stripe':
      return {
        icon: <CreditCard className="w-4 h-4" />,
        label: 'Web',
        color: 'text-blue-700',
        bgColor: 'bg-blue-100'
      };
    case 'apple_iap':
      return {
        icon: <Apple className="w-4 h-4" />,
        label: 'iOS',
        color: 'text-gray-700',
        bgColor: 'bg-gray-100'
      };
    case 'google_play':
      return {
        icon: <Smartphone className="w-4 h-4" />,
        label: 'Android',
        color: 'text-green-700',
        bgColor: 'bg-green-100'
      };
    case 'admin_grant':
      return {
        icon: <Gift className="w-4 h-4" />,
        label: '贈送',
        color: 'text-purple-700',
        bgColor: 'bg-purple-100'
      };
    case 'unknown':
    default:
      return {
        icon: <HelpCircle className="w-4 h-4" />,
        label: '未知',
        color: 'text-gray-500',
        bgColor: 'bg-gray-50'
      };
  }
}

/**
 * 付款平台 Badge 組件
 */
export function PaymentPlatformBadge({ platform }: { platform: PaymentPlatform | null | undefined }) {
  const info = getPaymentPlatformInfo(platform);

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${info.bgColor} ${info.color}`}>
      {info.icon}
      {info.label}
    </span>
  );
}

/**
 * 獲取付款平台的詳細文字說明
 */
export function getPaymentPlatformDescription(platform: PaymentPlatform | null | undefined): string {
  switch (platform) {
    case 'stripe':
      return 'Web 付款（信用卡、支付寶等）';
    case 'apple_iap':
      return 'iOS 應用內購買';
    case 'google_play':
      return 'Android Google Play 付款';
    case 'admin_grant':
      return '管理員贈送（免費）';
    case 'unknown':
    default:
      return '未知付款方式';
  }
}
