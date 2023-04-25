import { Component } from '@angular/core';
import { NgxSpinnerService } from 'ngx-spinner';
import { ToastrService } from 'ngx-toastr';
import { IawsService } from 'src/app/services/iaws.service';
import { FileSaverService } from 'ngx-filesaver';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'DataView';
  tweets: any[] = [];
  hashtags: any[] = [];

  constructor(
    private iaService: IawsService,
    private toastr: ToastrService,
    private fileServerService: FileSaverService,
    private spinner: NgxSpinnerService) { }

  ngOnInit(): void {
    this.get_tweets();
  }

  get_tweets() {
    this.spinner.show();
    this.iaService.get_all_tweets().then((r: any) => {
      this.spinner.hide();
      this.tweets = r.response;
      this.get_hashtags();
    }).catch((e: any) => { console.log(e); });
  }

  get_hashtags() {
    this.spinner.show();
    this.iaService.get_hashtags().then((r: any) => {
      this.spinner.hide();
      this.hashtags = r.response;
    }).catch((e: any) => { console.log(e); });
  }

  classify_tweet(tweet_id: Number, classification: string) {
    this.iaService.update_tweet(tweet_id, classification).then((r: any) => {
      this.get_tweets();
    }).catch((e: any) => { console.log(e); });
  }

  download_hashtags() {
    this.download(JSON.stringify(this.hashtags), 'hashtags.json');
  }

  download_tweets() {
    this.download(JSON.stringify(this.tweets), 'tweets.json');
  }

  upload_hashtags() {
    // listo
  }

  upload_tweets() {
    // listo
  }

  // <input type="file" (change)="onFileSelected($event)">

  onFileSelected(event: any) {
    const file = event.target.files[0];
    this.readFileContent(file);
  }

  private readFileContent(file: File) {
    const reader = new FileReader();
    reader.onload = () => {
      const content = reader.result as string;
      console.log(content);
    };
    reader.readAsText(file);
  }

  download(content: any, filename: any) {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    this.fileServerService.save(blob, filename);
    this.toastr.success('Archivo descargado', 'Satisfactoriamente');
  }
}
