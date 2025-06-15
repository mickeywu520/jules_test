import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../service/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-purchase',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './purchase.component.html',
  styleUrl: './purchase.component.css'
})
export class PurchaseComponent implements OnInit {
  constructor(private apiService: ApiService, private router: Router){}

  products: any[] = []
  suppliers: any[] = []
  productId:string = ''
  supplierId:string = ''
  description:string = ''
  quantity:string = ''
  message:string = ''
  

  ngOnInit(): void {
    // Subscribe to products from ApiService
    this.apiService.products$.subscribe((prods: any[]) => {
      this.products = prods;
    });
    this.apiService.fetchAndBroadcastProducts().subscribe({
      next: () => { /* console.log('Initial products fetched for PurchaseComponent'); */ },
      error: (err) => this.showMessage(err?.error?.message || err?.message || 'Unable to fetch initial products')
    });

    // Subscribe to suppliers from ApiService
    this.apiService.suppliers$.subscribe((supps: any[]) => {
      this.suppliers = supps;
    });
    this.apiService.fetchAndBroadcastSuppliers().subscribe({
      next: () => { /* console.log('Initial suppliers fetched for PurchaseComponent'); */ },
      error: (err) => this.showMessage(err?.error?.message || err?.message || 'Unable to fetch initial suppliers')
    });
  }

  //Handle form submission
  handleSubmit():void{
    if (!this.productId || !this.supplierId || !this.quantity) {
      this.showMessage("Please fill all fields")
      return;
    }
    const quantityInt = parseInt(this.quantity, 10);
    const productIdInt = parseInt(this.productId, 10);
    const supplierIdInt = parseInt(this.supplierId, 10);

    // Find the product to get its price
    const product = this.products.find(p => p.id === productIdInt);
    const totalPrice = product ? product.price * quantityInt : 0;

    const body = {
      products_involved: [{
        product_id: productIdInt,
        quantity: quantityInt
      }],
      totalProducts: quantityInt, // Assuming totalProducts is just the quantity for a single product transaction
      totalPrice: totalPrice,
      transactionType: 'PURCHASE',
      supplier_id: supplierIdInt,
      description: this.description
    }

    this.apiService.purchaseProduct(body).subscribe({
      next: (res: any) => {
        this.showMessage("Purchase successful!") // Use a generic success message as res.message might not exist
        // Optionally refresh product list in ApiService to reflect any changes (e.g. stock changes are backend-only but other details)
        this.apiService.fetchAndBroadcastProducts().subscribe({
          next: () => { /* console.log('Product list refreshed after purchase'); */ },
          error: (err: any) => { console.error('Failed to refresh product list after purchase:', err); }
        });
        this.resetForm();
        this.router.navigate(['/transaction']); // Navigate to transactions page
      },
      error: (error) => {
        this.showMessage(
          error?.error?.message ||
            error?.message ||
            'Unable to get purchase a product' + error
        );
      },
    })

  }

  
  resetForm():void{
    this.productId = '';
    this.supplierId = '';
    this.description = '';
    this.quantity = '';
  }


  



  showMessage(message: string) {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }
}
