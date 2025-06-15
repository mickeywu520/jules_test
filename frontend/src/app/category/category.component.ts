import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../service/api.service';

interface Category {
  id: string,
  name:string
}


@Component({
  selector: 'app-category',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './category.component.html',
  styleUrl: './category.component.css'
})

export class CategoryComponent implements OnInit {

  categories: Category[] = [];
  categoryName:string = '';
  message: string = '';
  isEditing:boolean = false;
  editingCategoryId:string | null = null;

  constructor(private apiService: ApiService){}

  ngOnInit(): void {
    this.apiService.categories$.subscribe((cats: Category[]) => {
      this.categories = cats;
    });
    // Fetch initial categories and populate/update the BehaviorSubject
    this.apiService.fetchAndBroadcastCategories().subscribe({
      next: (res: any) => {
        // console.log('Initial categories fetched by CategoryComponent');
      },
      error: (error: any) => {
        this.showMessage(error?.error?.message || error?.message || "Unable to fetch initial categories" + error);
      }
    });
  }


  //ADD A NEW CATEGORY
  addCategory():void{
    if (!this.categoryName) {
      this.showMessage("Category name is required");
      return;
    }
    this.apiService.createCategory({name:this.categoryName}).subscribe({
      next:(res:any) =>{
        this.showMessage("Category added successfully")
        this.categoryName = '';
        this.apiService.fetchAndBroadcastCategories().subscribe({
          next: () => { /* console.log('Categories refreshed after action'); */ },
          error: (err: any) => {
            console.error('Failed to refresh categories after action:', err);
            this.showMessage('Failed to refresh categories list.');
          }
        });
      },
      error:(error) =>{
        this.showMessage(error?.error?.message || error?.message || "Unable to save category" + error)
      }
    })
  }





  // EDIT CATEGORY
  editCategory():void{
    if (!this.editingCategoryId || !this.categoryName) {
      return;
    }
    this.apiService.updateCategory(this.editingCategoryId, {name:this.categoryName}).subscribe({
      next:(res:any) =>{
        this.showMessage("Category updated successfully")
        this.categoryName = '';
        this.isEditing = false;
        this.apiService.fetchAndBroadcastCategories().subscribe({
          next: () => { /* console.log('Categories refreshed after action'); */ },
          error: (err: any) => {
            console.error('Failed to refresh categories after action:', err);
            this.showMessage('Failed to refresh categories list.');
          }
        });
      },
      error:(error) =>{
        this.showMessage(error?.error?.message || error?.message || "Unable to edit category" + error)
      }
    })
  }

  //set the category to edit
  handleEditCategory(category:Category):void{
    this.isEditing = true;
    this.editingCategoryId = category.id;
    this.categoryName = category.name
  }

  //Delete a caetgory
  handleDeleteCategory(caetgoryId: string):void{
    if (window.confirm("Are you sure you want to delete this categoy?")) {
      this.apiService.deleteCategory(caetgoryId).subscribe({
        next:(res:any) =>{
          this.showMessage("Category deleted successfully")
          this.apiService.fetchAndBroadcastCategories().subscribe({
            next: () => { /* console.log('Categories refreshed after action'); */ },
            error: (err: any) => {
              console.error('Failed to refresh categories after action:', err);
              this.showMessage('Failed to refresh categories list.');
            }
          }); //reload the category
        },
        error:(error) =>{
          this.showMessage(error?.error?.message || error?.message || "Unable to Delete category" + error)
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
