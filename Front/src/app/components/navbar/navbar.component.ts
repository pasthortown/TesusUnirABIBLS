import { Component, OnInit } from '@angular/core';
import { environment } from 'src/environments/environment';
import { ExporterService } from 'src/app/services/exporter.service';
import { NgxSpinnerService } from 'ngx-spinner';
import { FileSaverService } from 'ngx-filesaver';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent implements OnInit {

  api_assets: string = environment.api_assets;

  constructor(
    private exporterService: ExporterService,
    private fileServerService: FileSaverService,
    private spinner: NgxSpinnerService) {
  }

  ngOnInit() {
  }

  ngOnChanges() {
  }

  imprimir_reporte() {
    let sign: any = {
      Construido_por: 'Monitoreo del Discurso XenofObico en Twitter',
      Fecha: new Date().toISOString(),
      Tesis: 'BECERRA JARAMILLO, DANIEL ISAI; BENALCÁZAR ROMÁN, ALEXANDER; SALAZAR VACA, LUIS ALFONSO'
    };
    let fecha_actual: any = {
      year: (new Date()).getFullYear(),
      month: (new Date()).getMonth() + 1,
      day: (new Date()).getDate()
    };
    let meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
    this.spinner.show();
    this.exporterService.build_qr(sign).then(qr_response => {
      this.spinner.hide();
      let tweets: any[] = JSON.parse(sessionStorage.getItem('tweets') as string);
      let params: any = {
        qr: qr_response.response,
        fecha: fecha_actual.day + ' de ' + meses[fecha_actual.month] + ' de ' + fecha_actual.year,
        tweets: tweets,
        hashtags_img: sessionStorage.getItem('cloudword_img'),
        lines_chart: sessionStorage.getItem('linechart_img'),
        bars_chart: sessionStorage.getItem('barchart_img'),
        radar_chart: sessionStorage.getItem('radarchart_img')
      };
      this.spinner.show();
      this.exporterService.build_pdf(params, 'report.html').then( r_exporter => {
        this.spinner.hide();
        if (r_exporter.status == 200) {
          let file: any = {
            file_base64: r_exporter.response,
            name: 'monitoreo_discurso_xenofobico_' + fecha_actual.year + '_' + fecha_actual.month + '_' + fecha_actual.day+ '.pdf'
          };
          this.download(file);
        }
      }).catch(e => { console.log(e); });
    }).catch(e => { console.log(e); });
  }

  download(item: any) {
    const byteCharacters = atob(item.file_base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
       byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: item.type});
    this.fileServerService.save(blob, item.name);
  }
}
