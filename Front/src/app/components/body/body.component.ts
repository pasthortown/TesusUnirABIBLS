import { Component, OnInit } from '@angular/core';
import { NgxSpinnerService } from 'ngx-spinner';
import { ToastrService } from 'ngx-toastr';
import { CloudData } from 'angular-tag-cloud-module';
import { ChartConfiguration, ChartOptions } from "chart.js";
import { ExporterService } from 'src/app/services/exporter.service';
import { IawsService } from 'src/app/services/iaws.service';

@Component({
  selector: 'app-body',
  templateUrl: './body.component.html',
  styleUrls: ['./body.component.scss']
})
export class BodyComponent implements OnInit{

  ready_cloud_data: boolean = false;
  ready_tweet_data: boolean = false;

  cloud_data: CloudData[] = [];

  lineChartData: ChartConfiguration<'line'>['data'] = {
    labels: [],
    datasets: []
  };
  lineChartOptions: ChartOptions<'line'> = {
    responsive: false
  };
  lineChartLegend = true;

  barChartLegend = true;
  barChartPlugins = [];
  barChartData: ChartConfiguration<'bar'>['data'] = {
    labels: [],
    datasets: []
  };
  barChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: false,
  };

  radarChartOptions: ChartConfiguration<'radar'>['options'] = {
    responsive: false,
  };
  radarChartLabels: string[] = [];
  radarChartDatasets: ChartConfiguration<'radar'>['data']['datasets'] = [];

  constructor(
    private exporterServive: ExporterService,
    private iaService: IawsService,
    private toastr: ToastrService,
    private spinner: NgxSpinnerService) { }

  ngOnInit(): void {
    this.toastr.success('Prueba de Toaster', 'Exito');
    this.spinner.show();
    this.get_data();
    setTimeout(() => {
      this.spinner.hide();
    }, 5000);
  }

  get_data() {
    this.get_hashtags();
    this.get_tweets();
  }

  get_hashtags() {
    this.iaService.hashtags().then((r: any) => {
      this.cloud_data = r.response;
      this.ready_cloud_data = true;
    }).catch(e => { console.log(e); });
  }

  get_tweets() {
    this.iaService.tweets().then((r: any) => {
      let data = r.response;
      this.lineChartData = {
        labels: data.lineChartLabels,
        datasets: data.lineChartDatasets
      };
      this.barChartData = {
        labels: data.barChartLabels,
        datasets: data.barChartDatasets
      };
      this.radarChartLabels = data.radarChartLabels;
      this.radarChartDatasets = data.radarChartDatasets;
      this.ready_tweet_data = true;
    }).catch(e => { console.log(e); });
  }
}
