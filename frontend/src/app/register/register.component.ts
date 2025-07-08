import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../service/api.service';
import { LoadingService } from '../service/loading.service';
import { firstValueFrom } from 'rxjs';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, CommonModule, RouterLink, TranslateModule],
  templateUrl: './register.component.html',
  styleUrl: './register.component.css'
})

export class RegisterComponent {
  constructor(
    private apiService: ApiService,
    private router: Router,
    private translate: TranslateService,
    private loadingService: LoadingService
  ){}

  formData: any = {
    email: '',
    name: '',
    phoneNumber: '',
    password: ''
  };
  message:string | null = null;
  messageType: 'success' | 'error' = 'error';

  async handleSubmit(){
    if(
      !this.formData.email ||
      !this.formData.name ||
      !this.formData.phoneNumber ||
      !this.formData.password
    ){
      this.showMessage("All fields are required", 'error');
      return;
    }

    // 顯示註冊loading
    this.loadingService.showRegistering();

    try {
      const payload_for_api = {
        ...this.formData,
        phoneNumber: String(this.formData.phoneNumber)
      };

      console.log('發送註冊請求，資料:', payload_for_api);

      const response: any = await firstValueFrom(
        this.apiService.registerUser(payload_for_api)
      );

      console.log('註冊回應:', response);

      // 註冊成功：後端返回用戶物件（包含 id, email, name 等）
      if (response && response.id) {
        console.log('註冊成功，用戶 ID:', response.id);

        // 顯示成功訊息
        const successMessage = this.translate.instant('REGISTER_SUCCESS_MESSAGE');
        this.showMessage(successMessage, 'success');

        console.log('顯示成功訊息，2秒後跳轉到登入頁面');

        // 隱藏loading並延遲跳轉，讓用戶看到成功訊息
        this.loadingService.hideLoading();
        setTimeout(() => {
          console.log('開始跳轉到登入頁面');
          this.router.navigate(["/login"]);
        }, 2000);
      } else {
        console.log('註冊回應格式不符預期:', response);
        // 如果回應格式不符預期
        this.loadingService.hideLoading();
        this.showMessage("註冊過程中發生未知錯誤", 'error');
      }
    } catch (error:any) {
      this.loadingService.hideLoading();
      console.log('Registration error:', error);

      // 處理不同類型的錯誤
      const errorMessage = error?.error?.message || error?.error?.detail || error?.message || "註冊失敗，請稍後再試";

      this.showMessage(errorMessage, 'error');
    }
  }

  showMessage(message:string, type: 'success' | 'error' = 'error'){
    this.message = message;
    this.messageType = type;

    // 成功訊息顯示較短時間，錯誤訊息顯示較長時間
    const timeout = type === 'success' ? 2500 : 4000;

    setTimeout(() =>{
      this.message = null
    }, timeout)
  }

}
