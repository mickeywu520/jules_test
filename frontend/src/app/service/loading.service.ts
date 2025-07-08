import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LoadingService {
  private loadingSubject = new BehaviorSubject<boolean>(false);
  private messageSubject = new BehaviorSubject<string>('讀取資料中...');

  // Observable for components to subscribe to loading state
  public isLoading$: Observable<boolean> = this.loadingSubject.asObservable();
  public message$: Observable<string> = this.messageSubject.asObservable();

  constructor() { }

  /**
   * Show loading dialog with optional custom message
   * @param message Custom loading message (default: '讀取資料中...')
   */
  showLoading(message: string = '讀取資料中...'): void {
    this.messageSubject.next(message);
    this.loadingSubject.next(true);
  }

  /**
   * Hide loading dialog
   */
  hideLoading(): void {
    this.loadingSubject.next(false);
  }

  /**
   * Get current loading state
   * @returns boolean indicating if loading is active
   */
  isLoading(): boolean {
    return this.loadingSubject.value;
  }

  /**
   * Show loading for specific operations
   */
  showDataLoading(): void {
    this.showLoading('讀取資料中...');
  }

  showSaving(): void {
    this.showLoading('儲存中...');
  }

  showDeleting(): void {
    this.showLoading('刪除中...');
  }

  showUpdating(): void {
    this.showLoading('更新中...');
  }

  showSearching(): void {
    this.showLoading('搜尋中...');
  }

  showLoggingIn(): void {
    this.showLoading('登入中...');
  }

  showRegistering(): void {
    this.showLoading('註冊中...');
  }
}
