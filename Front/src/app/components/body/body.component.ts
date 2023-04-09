import { Component, OnInit } from '@angular/core';
import { NgxSpinnerService } from 'ngx-spinner';
import { ToastrService } from 'ngx-toastr';
import { CloudData, CloudOptions } from 'angular-tag-cloud-module';
import { ChartConfiguration, ChartOptions, ChartType } from "chart.js";

@Component({
  selector: 'app-body',
  templateUrl: './body.component.html',
  styleUrls: ['./body.component.scss']
})
export class BodyComponent implements OnInit{

  cloud_data: CloudData[] = [
    { text: 'palabra1', weight: 5, rotate: 10, color: '#ffaaee' },
    { text: 'palabra2', weight: 7, rotate: -10, color: '#ffaaee' },
    { text: 'palabra3', weight: 9, rotate: 25, color: '#ffaaee' },
    { text: 'palabra4', weight: 7, rotate: -25 },
    { text: 'palabra5', weight: 5, rotate: 10 },
    { text: 'palabra6', weight: 7, rotate: -10 },
    { text: 'palabra7', weight: 9, rotate: 25 },
    { text: 'palabra8', weight: 7, rotate: -25 }
  ];

  lineChartData: ChartConfiguration<'line'>['data'] = {
    labels: [
      'Enero',
      'Febrero',
      'Marzo',
      'Abril',
      'Mayo',
      'Junio',
      'Julio'
    ],
    datasets: [
      {
        data: [ 65, 59, 80, 81, 56, 55, 40 ],
        label: '2021',
        fill: true,
        tension: 0.5
      },
      {
        data: [ 40, 55, 56, 81, 80, 59, 65 ],
        label: '2022',
        fill: true,
        tension: 0.5
      }
    ]
  };
  lineChartOptions: ChartOptions<'line'> = {
    responsive: false
  };
  lineChartLegend = true;

  barChartLegend = true;
  barChartPlugins = [];
  barChartData: ChartConfiguration<'bar'>['data'] = {
    labels: [ 'España', 'Ecuador', 'Estados Unidos', 'Alemania', 'Francia', 'Colombia', 'Brasil' ],
    datasets: [
      { data: [ 65, 59, 80, 81, 56, 55, 40 ], label: '2021' },
      { data: [ 28, 48, 40, 19, 86, 27, 90 ], label: '2022' }
    ]
  };
  barChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: false,
  };

  radarChartOptions: ChartConfiguration<'radar'>['options'] = {
    responsive: false,
  };
  radarChartLabels: string[] = ['España', 'Ecuador', 'Estados Unidos', 'Alemania', 'Francia', 'Colombia', 'Brasil'];
  radarChartDatasets: ChartConfiguration<'radar'>['data']['datasets'] = [
    { data: [65, 59, 90, 81, 56, 55, 40], label: 'Hombres' },
    { data: [28, 48, 40, 19, 96, 27, 100], label: 'Mujeres' }
  ];

  constructor(
    private toastr: ToastrService,
    private spinner: NgxSpinnerService) { }

  ngOnInit(): void {
    this.toastr.success('Prueba de Toaster', 'Exito');
    this.spinner.show();

    setTimeout(() => {
      /** spinner ends after 5 seconds */
      this.spinner.hide();
    }, 5000);
  }
}
