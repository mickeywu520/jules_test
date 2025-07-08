import { Component, OnInit, OnDestroy } from '@angular/core';
import { PaginationComponent } from '../pagination/pagination.component';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ApiService } from '../service/api.service';
import { LoadingService } from '../service/loading.service';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { Subscription } from 'rxjs';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-transaction',
  standalone: true,
  imports: [PaginationComponent, FormsModule, CommonModule, TranslateModule],
  templateUrl: './transaction.component.html',
  styleUrl: './transaction.component.css'
})
export class TransactionComponent implements OnInit, OnDestroy {
  constructor(
    private apiService: ApiService,
    private router: Router,
    private loadingService: LoadingService
  ){}

  transactions: any[] = [];
  message: string = '';
  searchInput:string = '';
  valueToSearch:string = '';
  currentPage: number = 1;
  totalPages: number = 0;
  itemsPerPage: number = 10;

  // 訂閱管理
  private routerSubscription?: Subscription;
  private isLoading = false;

  ngOnInit(): void {
    this.loadTransactions();

    // Subscribe to router events to reload transactions when navigating back to this component
    // 但要避免重複調用
    this.routerSubscription = this.router.events.pipe(
      filter(event => event instanceof NavigationEnd && event.urlAfterRedirects === '/transaction')
    ).subscribe(() => {
      // 只有在不是初始載入時才重新載入
      if (this.transactions.length > 0) {
        this.loadTransactions();
      }
    });
  }

  ngOnDestroy(): void {
    // 清理訂閱
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }


  //FETCH Transactions

  loadTransactions(): void {
    // 避免重複loading
    if (this.isLoading) {
      return;
    }

    this.isLoading = true;
    this.loadingService.showDataLoading();
    this.apiService.getAllTransactions(this.valueToSearch).subscribe({
      next: (res: any) => {
        const transactions = res || [];

        this.totalPages = Math.ceil(transactions.length / this.itemsPerPage);

        this.transactions = transactions.slice(
          (this.currentPage - 1) * this.itemsPerPage,
          this.currentPage * this.itemsPerPage
        );
        this.isLoading = false;
        this.loadingService.hideLoading();
      },
      error: (error) => {
        this.showMessage(
          error?.error?.message ||
            error?.message ||
            'Unable to Get all Transactions ' + error
        );
        this.isLoading = false;
        this.loadingService.hideLoading();
      },
    });
  }



  //HANDLE SERCH
  handleSearch():void{
    this.currentPage = 1;
    this.valueToSearch = this.searchInput;
    this.loadingService.showSearching();
    this.loadTransactions()
  }

  //NAVIGATE TGO TRANSACTIONS DETAILS PAGE
  navigateTOTransactionsDetailsPage(transactionId: string):void{
    this.router.navigate([`/transaction/${transactionId}`])
  }

    //HANDLE PAGE CHANGRTE. NAVIGATR TO NEXT< PREVIOUS OR SPECIFIC PAGE CHANGE
    onPageChange(page: number): void {
      this.currentPage = page;
      this.loadTransactions();
    }
  



  //SHOW ERROR
  showMessage(message: string) {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }
}
