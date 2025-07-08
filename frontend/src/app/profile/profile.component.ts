import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../service/api.service';
import { LoadingService } from '../service/loading.service';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.css'
})
export class ProfileComponent implements OnInit {
  constructor(
    private apiService: ApiService,
    private loadingService: LoadingService
  ){}
  user: any = null;
  message: string = "";
  allUsers: any[] = [];
  isAdmin: boolean = false;
  editingUserId: number | null = null;
  editingUser: any = {};

  ngOnInit(): void {
    this.fetchUserInfo();
    this.checkAdminStatus();
  }

  fetchUserInfo():void{
    this.loadingService.showDataLoading();
    this.apiService.getLoggedInUserInfo().subscribe({
      next:(res)=>{
        this.user = res;
        // 如果是ADMIN，載入所有用戶資訊
        if (this.isAdmin) {
          this.fetchAllUsers();
        } else {
          this.loadingService.hideLoading();
        }
      },
      error: (error) => {
        this.showMessage(
          error?.error?.message ||
            error?.message ||
            'Unable to Get Profile Info' + error
        );
        this.loadingService.hideLoading();
      }
    })
  }

  checkAdminStatus(): void {
    this.isAdmin = this.apiService.isAdmin();
  }

  fetchAllUsers(): void {
    this.apiService.getAllUsers().subscribe({
      next: (users) => {
        this.allUsers = users;
        this.loadingService.hideLoading();
      },
      error: (error) => {
        this.showMessage(
          error?.error?.message ||
            error?.message ||
            '無法載入用戶列表'
        );
        this.loadingService.hideLoading();
      }
    });
  }



  //SHOW ERROR
  showMessage(message: string) {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }

  startEditUser(user: any): void {
    this.editingUserId = user.id;
    this.editingUser = {
      id: user.id,
      name: user.name || '',
      email: user.email,
      phoneNumber: user.phoneNumber || '',
      role: user.role
    };
  }

  cancelEdit(): void {
    this.editingUserId = null;
    this.editingUser = {};
  }

  saveUser(): void {
    if (!this.editingUser.name || !this.editingUser.email) {
      this.showMessage('姓名和郵箱不能為空');
      return;
    }

    // 防止設置為ADMIN角色
    if (this.editingUser.role === 'ADMIN') {
      this.showMessage('不能將用戶角色設置為ADMIN');
      return;
    }

    this.loadingService.showDataLoading();
    this.apiService.updateUser(this.editingUser.id, this.editingUser).subscribe({
      next: (updatedUser) => {
        // 更新本地用戶列表
        const index = this.allUsers.findIndex(u => u.id === this.editingUser.id);
        if (index !== -1) {
          this.allUsers[index] = updatedUser;
        }
        this.showMessage('用戶資訊更新成功');
        this.cancelEdit();
        this.loadingService.hideLoading();
      },
      error: (error) => {
        this.showMessage(
          error?.error?.message ||
            error?.message ||
            '更新用戶資訊失敗'
        );
        this.loadingService.hideLoading();
      }
    });
  }
}
