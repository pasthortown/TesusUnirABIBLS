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
  tweets_shown: any[] = [];
  hashtags: any[] = [];
  filter: string = 'all';

  constructor(
    private iaService: IawsService,
    private toastr: ToastrService,
    private fileServerService: FileSaverService,
    private spinner: NgxSpinnerService) { }

  ngOnInit(): void {
    this.get_tweets();
  }

  filter_change() {
    if (this.filter != 'all') {
      this.tweets_shown = this.tweets.filter(tweet => tweet.clasificado === this.filter);
    } else {
      this.tweets_shown = this.tweets;
    }
  }

  get_tweets() {
    this.spinner.show();
    this.iaService.get_all_tweets().then((r: any) => {
      this.spinner.hide();
      this.tweets = r.response;
      this.filter_change();
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

  upload_hashtags(event: any) {
    const file = event.target.files[0];
    const reader = new FileReader();
    reader.onload = () => {
      const content = reader.result as string;
      this.spinner.show();
      this.iaService.upload_hashtags_backup(JSON.parse(content)).then((r: any) => {
        this.spinner.hide();
        this.toastr.success('Carga Realizada Satisfactoriamente', 'Hashtags');
      }).catch((e: any) => { console.log(e); });
    };
    reader.readAsText(file);
  }

  upload_tweets(event: any) {
    const file = event.target.files[0];
    const reader = new FileReader();
    reader.onload = () => {
      const content = JSON.parse(reader.result as string);
      const tweets = content.map(({ _id: { $oid }, created_at, ...rest }: any) => {
        const createdAt = new Date(created_at.$date).toISOString();
        return {
          ...rest,
          created_at: createdAt
        };
      });
      this.spinner.show();
      this.iaService.upload_tweets_backup(tweets).then((r: any) => {
        this.spinner.hide();
        this.toastr.success('Carga Realizada Satisfactoriamente', 'Tweets');
      }).catch((e: any) => { console.log(e); });
    };
    reader.readAsText(file);
  }

  download(content: any, filename: any) {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    this.fileServerService.save(blob, filename);
    this.toastr.success('Archivo descargado', 'Satisfactoriamente');
  }
}
