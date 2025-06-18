import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../service/api.service';
import { firstValueFrom } from 'rxjs';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, CommonModule, RouterLink, TranslateModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  constructor(private apiService:ApiService, private router:Router){}

  formData: any = {
    email: '',
    password: ''
  };

  message:string | null = null;

  async handleSubmit(){
    if( 
      !this.formData.email || 
      !this.formData.password 
    ){
      this.showMessage("All fields are required");
      return;
    }

    try {
      const loginResponse: any = await firstValueFrom(
        this.apiService.loginUser(this.formData)
      );

      // If firstValueFrom completes without error, login was successful (HTTP 2xx)
      if (loginResponse && loginResponse.access_token) {
        this.apiService.encryptAndSaveToStorage('token', loginResponse.access_token);

        // Fetch user information to get the role
        const userInfoResponse: any = await firstValueFrom(
          this.apiService.getLoggedInUserInfo()
        );

        if (userInfoResponse && userInfoResponse.role) {
          this.apiService.encryptAndSaveToStorage('role', userInfoResponse.role);
        } else {
          // Handle case where role might not be in userInfoResponse, though it should be
          console.warn('Role not found in userInfoResponse');
          // Potentially store a default or leave it blank, affecting isAdmin checks
        }

        this.apiService.authStatuschanged.emit(); // Notify other components of auth change
        this.router.navigate(['/dashboard']);
      } else {
        // This case should ideally not be reached if loginResponse is successful and backend sends token
        this.showMessage('Login successful, but token not received.');
        console.error('Login successful but access_token not in response:', loginResponse);
      }
    } catch (error:any) {
      console.log(error)
      this.showMessage(error?.error?.message || error?.message || "Unable to Login a user" + error)
      
    }
  }

  showMessage(message:string){
    this.message = message;
    setTimeout(() =>{
      this.message = null
    }, 4000)
  }

}
