import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Tailwind 클래스 병합 유틸리티
 * 조건부 클래스 적용 시 유용
 * 
 * 사용 예시:
 * <div className={cn('p-4', isActive && 'bg-blue-500', className)} />
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * 딜레이 유틸리티 (async/await용)
 */
export const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * 로컬 스토리지 유틸리티
 */
export const storage = {
  get: <T>(key: string): T | null => {
    if (typeof window === 'undefined') return null;
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  },
  set: <T>(key: string, value: T): void => {
    if (typeof window === 'undefined') return;
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('LocalStorage 저장 실패:', error);
    }
  },
  remove: (key: string): void => {
    if (typeof window === 'undefined') return;
    window.localStorage.removeItem(key);
  },
};
