import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { PaginationComponent } from '../pagination/pagination.component';
import { ApiService } from '../service/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-product',
  standalone: true,
  imports: [CommonModule, PaginationComponent],
  templateUrl: './product.component.html',
  styleUrl: './product.component.css',
})
export class ProductComponent implements OnInit {
  constructor(private apiService: ApiService, private router: Router) {}
  products: any[] = [];
  message: string = '';
  currentPage: number = 1;
  totalPages: number = 0;
  itemsPerPage: number = 10;

  ngOnInit(): void {
    this.fetchProducts();
  }

  //FETCH PRODUCTS
  fetchProducts(): void {
    this.apiService.getAllProducts().subscribe({
      next: (res: any) => {
        const products = res.products || [];
        console.log(products[0].imageUrl)

        this.totalPages = Math.ceil(products.length / this.itemsPerPage);

        this.products = products.slice(
          (this.currentPage - 1) * this.itemsPerPage,
          this.currentPage * this.itemsPerPage
        );
        
      },
      error: (error) => {
        this.showMessage(
          error?.error?.message ||
            error?.message ||
            'Unable to edit category' + error
        );
      },
    });
  }

  //DELETE A PRODUCT
  handleProductDelete(productId: string): void {
    if (window.confirm('Are you sure you want to delete this product?')) {
      this.apiService.deleteProduct(productId).subscribe({
        next: (res: any) => {
          if (res.status === 200) {
            this.showMessage('Product deleted successfully');
            this.fetchProducts(); //reload the products
          }
        },
        error: (error) => {
          this.showMessage(
            error?.error?.message ||
              error?.message ||
              'Unable to Delete product' + error
          );
        },
      });
    }
  }

  //HANDLE PAGE CHANGRTE. NAVIGATR TO NEXT< PREVIOUS OR SPECIFIC PAGE CHANGE
  onPageChange(page: number): void {
    this.currentPage = page;
    this.fetchProducts();
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
