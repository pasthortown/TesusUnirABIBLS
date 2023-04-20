import { environment } from 'src/environments/environment';
import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  assets = environment.api_assets;
  title = 'Monitoreo de Discurso Xenofóbico en Twitter';
}
