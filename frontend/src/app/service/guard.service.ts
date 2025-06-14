import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { ActivatedRouteSnapshot, CanActivate, GuardResult, MaybeAsync, Router, RouterStateSnapshot } from '@angular/router';


@Injectable({
  providedIn: 'root'
})

export class GuardService implements CanActivate {

  constructor(private apiService: ApiService, private router: Router) { }

  canActivate(
    route: ActivatedRouteSnapshot,
     state: RouterStateSnapshot): boolean {

    const requiresAdmin = route.data['requiresAdmin'] || false;

    if (requiresAdmin) {
      if (this.apiService.isAdmin()) {
        return true;
      }else{
        this.router.navigate(['/login'], {
          queryParams:{returnUrl: state.url}
        });
        return false;
      }
    }else{
      if (this.apiService.isAuthenticated()) {
        return true;
      }else{
        this.router.navigate(['/login'], {
          queryParams:{returnUrl: state.url}
        });
        return false; //deny access
      }
    }
  }
}
