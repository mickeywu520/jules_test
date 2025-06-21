import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../service/api.service';
import { ActivatedRoute, Router } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-add-edit-product',
  standalone: true,
  imports: [FormsModule, CommonModule, TranslateModule],
  templateUrl: './add-edit-product.component.html',
  styleUrl: './add-edit-product.component.css',
})
export class AddEditProductComponent implements OnInit {
  constructor(
    private apiService: ApiService,
    private route: ActivatedRoute,
    private router: Router
  ){}

  productId: string | null = null
  productCode: string = ''
  productName: string = ''
  unit: string = ''
  warehouse: string = ''
  unitWeight: string = ''
  barcode: string = ''
  categoryId: string = ''
  isEditing: boolean = false
  categories: any[] = []
  message: string = ''

  // 單位選項
  unitOptions = [
    { value: '箱', label: 'BOX' },
    { value: '盒', label: 'PACKAGE' },
    { value: '包', label: 'BAG' },
    { value: '瓶', label: 'BOTTLE' },
    { value: '罐', label: 'CAN' },
    { value: '袋', label: 'SACK' },
    { value: '個', label: 'PIECE' }
  ];



  ngOnInit(): void {
    this.productId = this.route.snapshot.paramMap.get('productId');
    this.fetchCategories();
    if (this.productId) {
      this.isEditing = true;
      this.fetchProductById(this.productId)
    }
  }


  // 獲取所有類別
  fetchCategories(): void {
    this.apiService.categories$.subscribe((cats: any[]) => {
      this.categories = cats;
    });
    this.apiService.fetchAndBroadcastCategories().subscribe({
      next: (res: any) => {
        // Categories loaded successfully
      },
      error: (error: any) => {
        this.showMessage(error?.error?.message || error?.message || "Unable to fetch categories" + error);
      }
    });
  }

  // 根據 ID 獲取產品資料
  fetchProductById(productId: string): void {
    this.apiService.getProductById(productId).subscribe({
      next: (res: any) => {
        const product = res;
        this.productCode = product.productCode || '';
        this.productName = product.productName || '';
        this.unit = product.unit || '';
        this.warehouse = product.warehouse || '';
        this.unitWeight = product.unitWeight || '';
        this.barcode = product.barcode || '';
        this.categoryId = product.category_id || '';
      },
      error: (error) => {
        this.showMessage(error?.error?.message || error?.message || "Unable to get product by id" + error)
      }
    })
  }

  handleSubmit(event: Event): void {
    event.preventDefault()

    // 驗證必填欄位
    if (!this.categoryId) {
      this.showMessage('請選擇類別');
      return;
    }

    if (!this.productCode || !this.productName || !this.unit) {
      this.showMessage('Product code, product name, and unit are required');
      return;
    }

    // 準備提交資料
    const productData = {
      productCode: this.productCode,
      productName: this.productName,
      unit: this.unit,
      warehouse: this.warehouse || null,
      unitWeight: parseFloat(this.unitWeight) || null,
      barcode: this.barcode || null,
      category_id: parseInt(this.categoryId)
    };

    if (this.isEditing) {
      this.apiService.updateProduct(this.productId!, productData).subscribe({
        next: (res: any) => {
          this.showMessage("Product updated successfully")
          // 刷新產品列表
          this.apiService.fetchAndBroadcastProducts().subscribe({
            next: () => { /* console.log('Product list refreshed after update'); */ },
            error: (err: any) => { console.error('Failed to refresh product list after update:', err); }
          });
          this.router.navigate(['/product'])
        },
        error: (error) => {
          this.showMessage(error?.error?.message || error?.message || "Unable to update product" + error)
        }
      })
    } else {
      this.apiService.addProduct(productData).subscribe({
        next: (res: any) => {
          this.showMessage("Product saved successfully")
          // 刷新產品列表
          this.apiService.fetchAndBroadcastProducts().subscribe({
            next: () => { /* console.log('Product list refreshed after add'); */ },
            error: (err: any) => { console.error('Failed to refresh product list after add:', err); }
          });
          this.router.navigate(['/product'])
        },
        error: (error) => {
          this.showMessage(error?.error?.message || error?.message || "Unable to save product" + error)
        }
      })
    }
  }





  showMessage(message:string){
    this.message = message;
    setTimeout(() =>{
      this.message = ''
    }, 4000)
  }


}
