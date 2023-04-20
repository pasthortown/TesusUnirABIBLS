import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';
import { NgxSpinnerService } from 'ngx-spinner';
import { ToastrService } from 'ngx-toastr';
import { CloudData } from 'angular-tag-cloud-module';
import { ChartConfiguration, ChartOptions } from "chart.js";
import { IawsService } from 'src/app/services/iaws.service';
import html2canvas from 'html2canvas';

@Component({
  selector: 'app-body',
  templateUrl: './body.component.html',
  styleUrls: ['./body.component.scss']
})
export class BodyComponent implements OnInit{
  @ViewChild('cloudword_div') cloudword_div: any;
  @ViewChild('linechart_div') linechart_div: any;
  @ViewChild('barchart_div') barchart_div: any;
  @ViewChild('radarchart_div') radarchart_div: any;

  cloudword_img: string = '';
  linechart_img: string = '';
  barchart_img: string = '';
  radarchart_img: string = '';

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
    private iaService: IawsService,
    private toastr: ToastrService,
    private spinner: NgxSpinnerService) { }

  ngOnInit(): void {
    this.get_data();
  }

  get_data() {
    this.spinner.show();
    this.get_hashtags();
    this.get_tweets();
  }

  get_hashtags() {
    this.ready_cloud_data = false;
    this.iaService.hashtags().then((r: any) => {
      this.cloud_data = r.response;
      this.ready_cloud_data = true;
      this.toastr.success('Datos cargados satisfactoriamente', 'Hashtags');
      if (this.ready_cloud_data && this.ready_tweet_data) {
        this.spinner.hide();
      }
    }).catch(e => { console.log(e); });
  }

  get_tweets() {
    this.ready_tweet_data = false;
    this.iaService.tweets().then((r: any) => {
      let data = r.response;
      sessionStorage.setItem('tweets', JSON.stringify(data.tweets));
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
      this.toastr.success('Datos cargados satisfactoriamente', 'Tweets');
      if (this.ready_cloud_data && this.ready_tweet_data) {
        setTimeout(() => {
          this.build_images_to_report();
        }, 2000);
      }
    }).catch(e => { console.log(e); });
  }

  build_images_to_report() {
    this.spinner.hide();
    html2canvas(this.cloudword_div.nativeElement).then((canvas) => {
      this.cloudword_img = canvas.toDataURL('image/png;base64');
      sessionStorage.setItem('cloudword_img', this.cloudword_img);
    });
    html2canvas(this.linechart_div.nativeElement).then((canvas) => {
      this.linechart_img = canvas.toDataURL('image/png;base64');
      sessionStorage.setItem('linechart_img', this.linechart_img);
    });
    html2canvas(this.barchart_div.nativeElement).then((canvas) => {
      this.barchart_img = canvas.toDataURL('image/png;base64');
      sessionStorage.setItem('barchart_img', this.barchart_img);
    });
    html2canvas(this.radarchart_div.nativeElement).then((canvas) => {
      this.radarchart_img = canvas.toDataURL('image/png;base64');
      sessionStorage.setItem('radarchart_img', this.radarchart_img);
    });
  }
}
