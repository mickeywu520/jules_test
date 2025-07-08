import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LoadingService } from '../service/loading.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-loading-dialog',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './loading-dialog.component.html',
  styleUrl: './loading-dialog.component.css'
})
export class LoadingDialogComponent implements OnInit, OnDestroy {
  isLoading = false;
  message = '讀取資料中...';
  
  private loadingSubscription?: Subscription;
  private messageSubscription?: Subscription;

  constructor(private loadingService: LoadingService) { }

  ngOnInit(): void {
    // Subscribe to loading state changes
    this.loadingSubscription = this.loadingService.isLoading$.subscribe(
      (loading: boolean) => {
        this.isLoading = loading;
      }
    );

    // Subscribe to message changes
    this.messageSubscription = this.loadingService.message$.subscribe(
      (message: string) => {
        this.message = message;
      }
    );
  }

  ngOnDestroy(): void {
    // Clean up subscriptions
    if (this.loadingSubscription) {
      this.loadingSubscription.unsubscribe();
    }
    if (this.messageSubscription) {
      this.messageSubscription.unsubscribe();
    }
  }
}
