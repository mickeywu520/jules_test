import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../service/api.service';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

interface Category {
  id: string,
  name:string
}


@Component({
  selector: 'app-category',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule],
  templateUrl: './category.component.html',
  styleUrl: './category.component.css'
})

export class CategoryComponent implements OnInit {

  categories: Category[] = [];
  categoryName:string = '';
  message: string = '';
  isEditing:boolean = false;
  editingCategoryId:string | null = null;

  constructor(private apiService: ApiService, private translate: TranslateService){}

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
        const errorMessage = error?.error?.message || error?.error?.detail || error?.message || this.translate.instant("UNABLE_TO_FETCH_INITIAL_CATEGORIES");
        this.showMessage(errorMessage);
      }
    });
  }


  //ADD A NEW CATEGORY
  addCategory():void{
    if (!this.categoryName) {
      this.showMessage(this.translate.instant("CATEGORY_NAME_REQUIRED"));
      return;
    }
    this.apiService.createCategory({name:this.categoryName}).subscribe({
      next:(res:any) =>{
        this.showMessage(this.translate.instant("CATEGORY_ADDED_SUCCESSFULLY"))
        this.categoryName = '';
        this.apiService.fetchAndBroadcastCategories().subscribe({
          next: () => { /* console.log('Categories refreshed after action'); */ },
          error: (err: any) => {
            console.error('Failed to refresh categories after action:', err);
            this.showMessage(this.translate.instant('FAILED_TO_REFRESH_CATEGORIES_LIST'));
          }
        });
      },
      error:(error) =>{
        const errorMessage = error?.error?.message || error?.error?.detail || error?.message || this.translate.instant("UNABLE_TO_SAVE_CATEGORY");
        this.showMessage(errorMessage);
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
        this.showMessage(this.translate.instant("CATEGORY_UPDATED_SUCCESSFULLY"))
        this.categoryName = '';
        this.isEditing = false;
        this.apiService.fetchAndBroadcastCategories().subscribe({
          next: () => { /* console.log('Categories refreshed after action'); */ },
          error: (err: any) => {
            console.error('Failed to refresh categories after action:', err);
            this.showMessage(this.translate.instant('FAILED_TO_REFRESH_CATEGORIES_LIST'));
          }
        });
      },
      error:(error) =>{
        const errorMessage = error?.error?.message || error?.error?.detail || error?.message || this.translate.instant("UNABLE_TO_EDIT_CATEGORY");
        this.showMessage(errorMessage);
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
    if (window.confirm(this.translate.instant("CONFIRM_DELETE_CATEGORY"))) {
      this.apiService.deleteCategory(caetgoryId).subscribe({
        next:(res:any) =>{
          this.showMessage(this.translate.instant("CATEGORY_DELETED_SUCCESSFULLY"))
          this.apiService.fetchAndBroadcastCategories().subscribe({
            next: () => { /* console.log('Categories refreshed after action'); */ },
            error: (err: any) => {
              console.error('Failed to refresh categories after action:', err);
              this.showMessage(this.translate.instant('FAILED_TO_REFRESH_CATEGORIES_LIST'));
            }
          }); //reload the category
        },
        error:(error) =>{
          const errorMessage = error?.error?.message || error?.error?.detail || error?.message || this.translate.instant("UNABLE_TO_DELETE_CATEGORY");
          this.showMessage(errorMessage);
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
