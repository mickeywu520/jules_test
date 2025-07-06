import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { Router, RouterLink, RouterOutlet, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { ApiService } from './service/api.service';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, CommonModule, TranslateModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})


export class AppComponent implements OnInit, AfterViewInit {
  title = 'ims';
  @ViewChild('navLinks', { static: false }) navLinks!: ElementRef;
  sidebarOpen = false;

  constructor(
    private apiService: ApiService,
    private router: Router,
    private cdr: ChangeDetectorRef,
    private translate: TranslateService
  ) {
    this.translate.addLangs(['en', 'zh-TW']);
    this.translate.setDefaultLang('zh-TW');
  }


isAuth():boolean{
  return this.apiService.isAuthenticated();
}

isAdmin():boolean{
  return this.apiService.isAdmin();
}

logOut():void{
  this.apiService.logout();
  this.router.navigate(["/login"])
  this.cdr.detectChanges();
}

  ngOnInit(): void {
    this.apiService.getFastApiData().subscribe({
      next: (data) => console.log('Data from FastAPI backend:', data),
      error: (err) => console.error('Error fetching from FastAPI:', err)
    });

    // 監聽路由變化，自動關閉側邊欄
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => {
        this.closeSidebar();
      });
  }

  ngAfterViewInit(): void {
    // 初始化滾動功能
  }

  // 滑鼠滾輪事件處理
  onMouseWheel(event: WheelEvent): void {
    // 阻止事件冒泡，避免影響頁面滾動
    event.stopPropagation();

    if (!this.navLinks) return;

    const element = this.navLinks.nativeElement;
    const scrollAmount = 30; // 每次滾動的像素數

    if (event.deltaY > 0) {
      // 向下滾動
      element.scrollTop += scrollAmount;
    } else {
      // 向上滾動
      element.scrollTop -= scrollAmount;
    }

    // 阻止默認滾動行為
    event.preventDefault();
  }

  // 切換側邊欄顯示/隱藏
  toggleSidebar(): void {
    this.sidebarOpen = !this.sidebarOpen;
  }

  // 關閉側邊欄
  closeSidebar(): void {
    this.sidebarOpen = false;
  }

  // 導航項目點擊處理
  onNavItemClick(): void {
    this.closeSidebar();
  }





}
