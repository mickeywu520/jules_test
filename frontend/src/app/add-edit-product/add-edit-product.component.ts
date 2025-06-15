import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../service/api.service';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-add-edit-product',
  standalone: true,
  imports: [FormsModule, CommonModule],
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
  name:string = ''
  sku:string = ''
  price:string = ''
  stockQuantity:string = ''
  categoryId:string = ''
  description:string = ''
  imageFile:File | null = null
  imageUrl:string = ''
  isEditing:boolean = false
  categories:any[] = []
  message:string = ''



  ngOnInit(): void {
    this.productId = this.route.snapshot.paramMap.get('productId');
    this.fetchCategories();
    if (this.productId) {
      this.isEditing = true;
      this.fetchProductById(this.productId)
    }
  }


  //GET ALL CATEGORIES
  fetchCategories():void{
    this.apiService.categories$.subscribe((cats: any[]) => {
      this.categories = cats;
    });
    // Ensure categories are fetched if not already, or to get latest
    this.apiService.fetchAndBroadcastCategories().subscribe({
      next: (res: any) => {
        // console.log('Categories fetched for AddEditProductComponent');
        // The BehaviorSubject in ApiService is now updated.
        // this.categories will be updated by the categories$ subscription.
      },
      error: (error: any) => {
        this.showMessage(error?.error?.message || error?.message || "Unable to fetch categories for product form" + error);
      }
    });
  }


  //GET CATEGORY BY ID

  fetchProductById(productId: string):void{
    this.apiService.getProductById(productId).subscribe({
      next:(res:any) =>{
        const product = res; // Direct assignment as backend returns product object directly
        this.name = product.name;
        this.sku = product.sku;
        this.price = product.price;
        this.stockQuantity = product.stockQuantity;
        this.categoryId = product.categoryId; // Corrected typo from caetgoryId
        this.description = product.description;
        this.imageUrl = product.imageUrl;
      },
      error:(error) =>{
        this.showMessage(error?.error?.message || error?.message || "Unable to get all categories" + error)
      }})
  }

  handleImageChange(event: Event):void{
    const input = event.target as HTMLInputElement;
    if (input?.files?.[0]) {
      this.imageFile = input.files[0]
      const reader = new FileReader();
      reader.onloadend = () =>{
        this.imageUrl = reader.result as string
      }
      reader.readAsDataURL(this.imageFile);
    }
  }

  handleSubmit(event : Event):void{
    event.preventDefault()
    const formData = new FormData();
    formData.append("name", this.name);
    formData.append("sku", this.sku);
    formData.append("price", this.price);
    formData.append("stockQuantity", this.stockQuantity);
    formData.append("categoryId", this.categoryId);
    formData.append("description", this.description);

    if (this.imageFile) {
      formData.append("imageFile", this.imageFile);
    }

    if (this.isEditing) {
      // Remove productId from formData as it's now passed in the URL
      // formData.append("productId", this.productId!); // This line is removed
      this.apiService.updateProduct(this.productId!, formData).subscribe({ // Pass productId as first argument
        next:(res:any) =>{
          this.showMessage("product updated successfully")
          // Refresh the product list in ApiService before navigating
          this.apiService.fetchAndBroadcastProducts().subscribe({
            next: () => { /* console.log('Product list refreshed after add/update'); */ },
            error: (err: any) => { console.error('Failed to refresh product list after add/update:', err); }
          });
          this.router.navigate(['/product'])
        },
        error:(error) =>{
          this.showMessage(error?.error?.message || error?.message || "Unable to update a product" + error)
        }})
    }else{
      this.apiService.addProduct(formData).subscribe({
        next:(res:any) =>{
          this.showMessage("Product Saved successfully")
          // Refresh the product list in ApiService before navigating
          this.apiService.fetchAndBroadcastProducts().subscribe({
            next: () => { /* console.log('Product list refreshed after add/update'); */ },
            error: (err: any) => { console.error('Failed to refresh product list after add/update:', err); }
          });
          this.router.navigate(['/product'])
        },
        error:(error) =>{
          this.showMessage(error?.error?.message || error?.message || "Unable to save a product" + error)
        }})

    }


  }





  showMessage(message:string){
    this.message = message;
    setTimeout(() =>{
      this.message = ''
    }, 4000)
  }


}
