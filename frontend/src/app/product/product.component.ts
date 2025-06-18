import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { PaginationComponent } from '../pagination/pagination.component';
import { ApiService } from '../service/api.service';
import { Router } from '@angular/router';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-product',
  standalone: true,
  imports: [CommonModule, PaginationComponent, TranslateModule],
  templateUrl: './product.component.html',
  styleUrl: './product.component.css',
})
export class ProductComponent implements OnInit {
  private fullProductList: any[] = [];
  constructor(private apiService: ApiService, private router: Router, private translate: TranslateService) {}
  products: any[] = [];
  message: string = '';
  currentPage: number = 1;
  totalPages: number = 0;
  itemsPerPage: number = 10;

  ngOnInit(): void {
    this.setupProductSubscriptionAndLoad();
  }

  // Renamed from fetchProducts to reflect new reactive approach
  setupProductSubscriptionAndLoad(): void {
    this.apiService.products$.subscribe((allProducts: any[]) => {
      this.fullProductList = allProducts; // Store the full list
      this.applyPagination(); // Apply pagination to the new full list
    });
    // Trigger initial load / refresh of products from backend
    this.apiService.fetchAndBroadcastProducts().subscribe({
      next: () => {
        // console.log('Initial products fetched for ProductComponent');
        // Data is now in BehaviorSubject, products$ subscription will handle it.
      },
      error: (error: any) => {
        this.showMessage(
          error?.error?.message ||
          error?.message ||
          this.translate.instant('UNABLE_TO_FETCH_INITIAL_PRODUCTS') + error
        );
      }
    });
  }

  applyPagination(): void {
    if (!this.fullProductList) return;
    this.totalPages = Math.ceil(this.fullProductList.length / this.itemsPerPage);
    this.products = this.fullProductList.slice(
      (this.currentPage - 1) * this.itemsPerPage,
      this.currentPage * this.itemsPerPage
    );
  }

  //DELETE A PRODUCT
  handleProductDelete(productId: string): void {
    if (window.confirm(this.translate.instant('CONFIRM_DELETE_PRODUCT'))) {
      this.apiService.deleteProduct(productId).subscribe({
        next: (res: any) => {
          this.showMessage(this.translate.instant('PRODUCT_DELETED_SUCCESSFULLY'));
          this.apiService.fetchAndBroadcastProducts().subscribe({
            next: () => { /* console.log('Products refreshed after delete'); */ },
            error: (err: any) => {
              console.error('Failed to refresh products after delete:', err);
              this.showMessage(this.translate.instant('FAILED_TO_REFRESH_PRODUCT_LIST'));
            }
          }); //reload the products
        },
        error: (error) => {
          this.showMessage(
            error?.error?.message ||
              error?.message ||
              this.translate.instant('UNABLE_TO_DELETE_PRODUCT') + error
          );
        },
      });
    }
  }

  //HANDLE PAGE CHANGRTE. NAVIGATR TO NEXT< PREVIOUS OR SPECIFIC PAGE CHANGE
  onPageChange(page: number): void {
    this.currentPage = page;
    this.applyPagination();
  }

  //NAVIGATE TO ADD PRODUCT PAGE
  navigateToAddProductPage(): void {
    this.router.navigate(['/add-product']);
  }

  //NAVIGATE TO EDIT PRODUCT PAGE
  navigateToEditProductPage(productId: string): void {
    this.router.navigate([`/edit-product/${productId}`]);
  }

  //SHOW ERROR
  showMessage(message: string) {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }
}
